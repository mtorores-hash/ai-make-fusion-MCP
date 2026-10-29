"""Durable same-user job protocol. No Autodesk imports: safe in MCP and worker threads."""
import ast
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import time
import uuid
from .execution_policy import validate_read_only, validate_reconciliation
from .compatibility import identity

ROOT = Path.home() / '.fusion-prompt-mcp'
TERMINAL = {'succeeded', 'failed', 'cancelled', 'interrupted'}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

class Store:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.db = self.root / 'jobs.sqlite3'
        with self.connect() as c:
            c.execute('PRAGMA journal_mode=WAL')
            c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY, operation_id TEXT UNIQUE NOT NULL,
                digest TEXT NOT NULL, request TEXT NOT NULL, status TEXT NOT NULL,
                created REAL NOT NULL, updated REAL NOT NULL, progress REAL NOT NULL DEFAULT 0,
                message TEXT NOT NULL DEFAULT '', cancel_requested INTEGER NOT NULL DEFAULT 0,
                result TEXT, owner TEXT)''')
            c.execute('CREATE TABLE IF NOT EXISTS activity (cursor INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, at REAL, kind TEXT, data TEXT)')
            c.execute('CREATE INDEX IF NOT EXISTS activity_job ON activity(job_id,cursor)')
            c.execute('CREATE TABLE IF NOT EXISTS heartbeat (owner TEXT PRIMARY KEY, at REAL, busy INTEGER)')

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.db, timeout=10)
        c.row_factory = sqlite3.Row
        try:
            with c:
                yield c
        finally:
            c.close()

    def submit(self, request):
        if not isinstance(request, dict): raise ValueError('request must be an object')
        for key in ('operation_id','document_id','component_token','units','script'):
            if not isinstance(request.get(key),str) or not request[key]:
                raise ValueError(key+' must be a nonempty string')
        for key in ('checkpoint_before','validate_after'):
            if type(request.get(key)) is not bool: raise ValueError(key+' must be boolean')
        mode=request.get('mode','modeling')
        if mode not in ('modeling','read_only','reconcile'): raise ValueError('mode must be modeling, read_only or reconcile')
        operation_id = request['operation_id']
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', operation_id):
            raise ValueError('operation_id must be 1–128 letters, digits, _, ., :, or -')
        if not request.get('document_id') or not request.get('component_token'):
            raise ValueError('Explicit document_id and component_token are required.')
        if request['units'] not in ('mm', 'cm', 'm', 'in'):
            raise ValueError('Unsupported units.')
        source = request['script']
        if len(source.encode()) > 2_000_000:
            raise ValueError('Script exceeds 2 MB.')
        tree = ast.parse(source, filename='<fusion-job>')
        if not any(isinstance(n, ast.FunctionDef) and n.name == 'run' for n in tree.body):
            raise ValueError('Script must define synchronous run(ctx).')
        if mode=='read_only':
            validate_read_only(tree)
            if request['checkpoint_before']:
                raise ValueError('read_only does not create checkpoints; set checkpoint_before=False')
        if mode=='reconcile':
            validate_reconciliation(tree)
            if request['checkpoint_before'] or request['validate_after']:
                raise ValueError('reconcile changes only ledger records; set checkpoint_before=False and validate_after=False')
            if not request.get('scope') or not request.get('task') or not request.get('edit_token'):
                raise ValueError('reconcile requires current scope, task.writer_id and a writer edit_token')
        task=request.get('task') or {}
        for key in ('scope','task'):
            if request.get(key) is not None and (not isinstance(request[key],dict) or not request[key]):
                raise ValueError(key+' must be a nonempty contract object or null')
        if task.get('max_seconds') is not None:
            bound=task['max_seconds']
            if type(bound) not in (int,float) or (not math.isfinite(bound) or bound<=0):raise ValueError('task.max_seconds must be finite and >0; cooperative only')
        # Preserve v0.3 idempotency digests for the unchanged default modeling behavior.
        request=dict(request)
        request['_caller']=identity()
        if request.get('mode')=='modeling': request.pop('mode')
        if not request.get('edit_token'): request.pop('edit_token',None)
        for optional in ('scope','task','accepted_reference_versions'):
            if request.get(optional) is None or (optional=='accepted_reference_versions' and request.get(optional)=={}):request.pop(optional,None)
        return self._enqueue(request)

    def submit_cloud(self, request):
        if not isinstance(request, dict): raise ValueError('request must be an object')
        op = request.get('operation_id', '')
        if not isinstance(op,str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',op):
            raise ValueError('Invalid operation_id')
        if request.get('action') not in ('ensure_project','ensure_folder','save','save_component','open','insert','update_reference'):
            raise ValueError('Unsupported cloud action')
        if not isinstance(request.get('arguments'),dict): raise ValueError('arguments must be an object')
        if len(canonical(request))>100_000: raise ValueError('Cloud request too large')
        return self._enqueue(dict(request,kind='cloud',_caller=identity()))

    def _enqueue(self, request):
        operation_id=request['operation_id']
        encoded = canonical(request)
        # Runtime metadata must not turn an uncertain retry into a different operation.
        digest = hashlib.sha256(canonical({k:v for k,v in request.items() if k!='_caller'}).encode()).hexdigest()
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            old = c.execute('SELECT * FROM jobs WHERE operation_id=?', (operation_id,)).fetchone()
            if old:
                if old['digest'] != digest:
                    raise ValueError('operation_id already used with different content. Use a NEW ID for a new operation.')
                return self.summary(old)
            now = time.time()
            job_id = uuid.uuid4().hex
            c.execute('INSERT INTO jobs(job_id,operation_id,digest,request,status,created,updated) VALUES(?,?,?,?,?,?,?)',
                      (job_id, operation_id, digest, encoded, 'queued', now, now))
        return self.status(job_id)

    def assert_no_uncertain_cloud(self, exclude_job_id=''):
        with self.connect() as c:
            rows=c.execute("SELECT job_id,result FROM jobs WHERE job_id!=? AND result IS NOT NULL",(exclude_job_id,)).fetchall()
        unresolved=[r['job_id'] for r in rows if json.loads(r['result']).get('uncertain')]
        if unresolved:raise ValueError('Uncertain cloud operations require original-job reconciliation before mutation: '+','.join(unresolved))

    def annotate_result(self, job_id, result):
        # Reconciliation records an observation, never rewrites the original execution status.
        with self.connect() as c:
            c.execute('UPDATE jobs SET result=?,updated=? WHERE job_id=?',(canonical(result),time.time(),job_id))

    def row(self, job_id):
        with self.connect() as c:
            r = c.execute('SELECT * FROM jobs WHERE job_id=?', (job_id,)).fetchone()
        if not r:
            raise ValueError('Unknown job_id.')
        return r

    @staticmethod
    def summary(row):
        return {k: row[k] for k in ('job_id','operation_id','status','created','updated',
                                   'progress','message','cancel_requested')}

    def status(self, job_id):
        row=self.row(job_id);result=self.summary(row)
        with self.connect() as c:
            event=c.execute('SELECT * FROM activity WHERE job_id=? ORDER BY cursor DESC LIMIT 1',(job_id,)).fetchone()
            beat=c.execute('SELECT * FROM heartbeat ORDER BY at DESC LIMIT 1').fetchone()
        data=json.loads(event['data']) if event else None
        if data:
            target=data.get('target')
            data={k:data[k] for k in ('operation','activity_id','status','elapsed_seconds','last_completed_stage') if k in data}
            if target is not None:data['target_preview']=str(target)[:512]
            for k in ('operation','last_completed_stage'):
                if k in data and data[k] is not None:data[k]=str(data[k])[:256]
            data['identities_and_checkpoint']='Retrieve job_result(section="events", offset=<cursor>) for full activity'
        result['activity']=dict(event,data=data) if event else None
        result['bridge_liveness']=dict(beat) if beat else None
        if beat:result['bridge_liveness'].update(age_seconds=max(0,time.time()-beat['at']),observed_fresh=time.time()-beat['at']<5)
        result['main_thread_last_activity_age_seconds']=max(0,time.time()-event['at']) if event else None
        result['liveness_note']='Heartbeat is worker liveness, not main-thread progress or completed geometry'
        result['cancellation']='acknowledged' if row['status']=='cancelled' else 'pending_cooperative_boundary' if row['cancel_requested'] else 'not_requested'
        return result

    def event(self,job_id,kind,data):
        with self.connect() as c:
            c.execute('INSERT INTO activity(job_id,at,kind,data) VALUES(?,?,?,?)',(job_id,time.time(),kind,canonical(data)))

    def events(self,job_id,after=0,limit=50):
        if type(after) is not int or after<0 or type(limit) is not int or not 1<=limit<=100:raise ValueError('Invalid activity cursor/page')
        with self.connect() as c:
            rows=c.execute('SELECT * FROM activity WHERE job_id=? AND cursor>? ORDER BY cursor LIMIT ?',(job_id,after,limit)).fetchall()
        return {'events':[dict(r,data=json.loads(r['data'])) for r in rows],
                'cursor':rows[-1]['cursor'] if rows else after,'unchanged':not rows,'limit':limit}

    def beat(self,owner,busy):
        with self.connect() as c:c.execute('INSERT OR REPLACE INTO heartbeat VALUES(?,?,?)',(owner,time.time(),int(busy)))

    def result(self, job_id):
        r = self.row(job_id)
        return dict(self.summary(r), result=json.loads(r['result']) if r['result'] else None)

    def list(self, limit=30):
        with self.connect() as c:
            rows = c.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT ?', (min(max(limit,1),100),)).fetchall()
        return [self.summary(r) for r in rows]

    def pending(self):
        with self.connect() as c:
            return c.execute("SELECT 1 FROM jobs WHERE status IN ('queued','waiting','running') LIMIT 1").fetchone() is not None

    def claim(self, owner):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute("SELECT * FROM jobs WHERE status IN ('queued','waiting') ORDER BY created LIMIT 1").fetchone()
            if not row:
                return None
            c.execute("UPDATE jobs SET status='running',owner=?,updated=?,message='Starting' WHERE job_id=?",
                      (owner, time.time(), row['job_id']))
        return dict(row, request=json.loads(row['request']))

    def waiting(self, message):
        with self.connect() as c:
            c.execute("UPDATE jobs SET status='waiting',message=?,updated=? WHERE status IN ('queued','waiting')",
                      (message, time.time()))

    def progress(self, job_id, fraction, message):
        if not 0 <= fraction <= 1:
            raise ValueError('Progress fraction must be between 0 and 1.')
        with self.connect() as c:
            c.execute("UPDATE jobs SET progress=?,message=?,updated=? WHERE job_id=? AND status='running'",
                      (fraction, str(message), time.time(), job_id))

    def partial(self, job_id, result):
        value = canonical(result)
        with self.connect() as c:
            c.execute("UPDATE jobs SET result=?,updated=? WHERE job_id=? AND status='running'", (value,time.time(),job_id))

    def finish(self, job_id, status, result):
        if status not in TERMINAL:
            raise ValueError('Invalid terminal status.')
        value = canonical(result)
        with self.connect() as c:
            c.execute("UPDATE jobs SET status=?,result=?,message=?,progress=?,updated=? WHERE job_id=? AND status='running'",
                      (status, value, result.get('message',status), 1 if status=='succeeded' else 0,
                       time.time(),job_id))

    def cancel(self, job_id):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute('SELECT * FROM jobs WHERE job_id=?',(job_id,)).fetchone()
            if not row: raise ValueError('Unknown job_id.')
            if row['status'] not in TERMINAL:
                status = 'cancelled' if row['status'] in ('queued','waiting') else row['status']
                c.execute('UPDATE jobs SET cancel_requested=1,status=?,updated=? WHERE job_id=?',
                          (status,time.time(),job_id))
        return self.status(job_id)

    def recover(self):
        # Called only after exclusive bridge lock acquired. Never auto-replay a running job.
        with self.connect() as c:
            if c.execute("SELECT 1 FROM sqlite_master WHERE name='authoring_issues'").fetchone():
                for issue in c.execute('SELECT issue_id,record FROM authoring_issues').fetchall():
                    record=json.loads(issue['record'])
                    if record.get('active_operation') and not record.get('interrupted_at'):
                        record['interrupted_at']=time.time()
                        c.execute('UPDATE authoring_issues SET record=? WHERE issue_id=?',(canonical(record),issue['issue_id']))
            for row in c.execute("SELECT job_id,result FROM jobs WHERE status='running'").fetchall():
                result=json.loads(row['result']) if row['result'] else {}
                result.setdefault('outcomes',{})['mutation']='uncertain_after_restart'
                result['replay_permitted']=False
                c.execute('UPDATE jobs SET result=? WHERE job_id=?',(canonical(result),row['job_id']))
                c.execute('INSERT INTO activity(job_id,at,kind,data) VALUES(?,?,?,?)',
                          (row['job_id'],time.time(),'interrupted',canonical({'effects':'uncertain','replayed':False})))
            c.execute("UPDATE jobs SET status='interrupted',message=?,updated=? WHERE status='running'",
                      ('Fusion bridge restarted during execution. Inspect/checkpoint recovery required; not replayed.',time.time()))

class BridgeLock:
    """OS lock released after a crash. Only one Fusion instance can own this queue."""
    def __init__(self, root=ROOT):
        self.path = Path(root) / 'bridge.lock'
        self.file = None
    def acquire(self):
        import os
        self.file = self.path.open('a+b')
        self.file.seek(0); self.file.write(b'0'); self.file.flush(); self.file.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close(); self.file=None
            raise RuntimeError('Another Fusion instance already owns the MCP bridge.')
    def close(self):
        if self.file:
            self.file.close(); self.file=None


def load_engineering_report(store,job_id):
    from .verification import file_hash
    job=store.result(job_id);record=(job.get('result') or {}).get('engineering_report')
    if not record:raise ValueError('Original job has no engineering report')
    path=Path(record['artifact']['path']).resolve();root=(store.root/'artifacts'/job_id).resolve()
    if not path.is_relative_to(root) or file_hash(path)!=record['artifact']['sha256']:
        raise ValueError('Engineering artifact missing, outside original job or modified')
    return json.loads(path.read_text(encoding='utf-8'))
