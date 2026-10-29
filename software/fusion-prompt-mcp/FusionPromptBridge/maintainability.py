"""Opt-in per-issue authoring budgets. Trusted Python is detected posthoc, not sandboxed."""
import json
import time
from . import advanced
from .job_store import canonical


def counts(selection,allowed):
    result={}
    for member,c in selection.entries:
        if member['id'] in allowed:
            result[member['id']]={name:[getattr(c,name).item(i) for i in range(getattr(c,name).count)]
                                  for name in ('features','sketches')}
    return result


class Guard:
    def __init__(self,store,design,selection,task,document_id,operation_id,path='trusted_python'):
        self.store=store;self.design=design;self.selection=selection;self.task=task or {};self.policy=self.task.get('authoring')
        self.operation_id=operation_id;self.path=path;self.started=None;self.record=None
        self.status={'status':'procedural_unbounded','enforcement':'No per-change budget adopted; native health does not establish maintainability'}
        # Omitting the optional policy must not clear an already-blocked scoped issue.
        if store and self.task.get('allowed_member_ids'):
            with store.connect() as c:
                c.execute('CREATE TABLE IF NOT EXISTS authoring_issues (issue_id TEXT PRIMARY KEY, record TEXT)')
                c.execute('CREATE TABLE IF NOT EXISTS authoring_claims (document_id TEXT, component_id TEXT, issue_id TEXT, PRIMARY KEY(document_id,component_id))')
                claims=c.execute('SELECT component_id,issue_id,record FROM authoring_claims JOIN authoring_issues USING(issue_id) WHERE document_id=?',(document_id,)).fetchall()
            for claim in claims:
                try:component=design.rootComponent if claim['component_id']=='@root' else advanced.resolve(design,claim['component_id'])
                except Exception:
                    if json.loads(claim['record']).get('blocked') or json.loads(claim['record']).get('active_operation'):
                        raise ValueError('Unresolved authoring claim has a stale component reference; reconcile its ownership before further authoring')
                    continue
                member=selection.member(component);prior=json.loads(claim['record'])
                if member and member['id'] in self.task['allowed_member_ids'] and (prior.get('blocked') or prior.get('active_operation')):
                    if not self.policy or claim['issue_id']!=self.task.get('issue_id'):
                        raise ValueError('Affected member has unresolved authoring issue '+claim['issue_id'])
        if not self.policy:return
        p=self.policy
        for k in ('max_new_features','max_new_sketches','cumulative_new_features','cumulative_new_sketches','max_attempts'):
            if type(p.get(k)) is not int or p[k]<0:raise ValueError('authoring.'+k+' must be an adopted nonnegative integer')
        if type(p.get('max_seconds')) not in (int,float) or not 0<p['max_seconds']<float('inf'):raise ValueError('Adopt a finite issue max_seconds')
        for k in ('source_feature_tokens','planned_operations'):
            if not isinstance(p.get(k),list) or not p[k]:raise ValueError('authoring.'+k+' required')
        if not p.get('strategy_revision') or not p.get('strategy_note') or not p.get('budget_reason'):raise ValueError('Named authoring strategy and budget reason required')
        if not isinstance(p.get('protected_member_ids'),list) or not set(p['protected_member_ids'])<=set(self.task.get('frozen_member_ids',[])):
            raise ValueError('authoring.protected_member_ids must name frozen task members (empty list is explicit)')
        self.issue=self.task.get('issue_id')
        if not self.issue:raise ValueError('Stable project-qualified task.issue_id required')
        self.allowed=set(self.task.get('allowed_member_ids',[]))
        self.before=counts(selection,self.allowed)
        if not self.before:raise ValueError('Budget needs affected permitted members')
        self.sources=[]
        for token in p['source_feature_tokens']:
            entity=advanced.resolve(design,token);owner=getattr(entity,'parentComponent',None)
            member=selection.member(owner)
            if not member or member['id'] not in self.allowed:raise ValueError('Source feature outside affected members')
            self.sources.append(entity)
        self.document_id=document_id
        from .authoring_recovery import snapshot
        attempt_snapshot=snapshot(design,selection,self.task)
        with store.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS authoring_issues (issue_id TEXT PRIMARY KEY, record TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS authoring_claims (document_id TEXT, component_id TEXT, issue_id TEXT, PRIMARY KEY(document_id,component_id))')
            c.execute('BEGIN IMMEDIATE')
            for m,component in selection.entries:
                if m['id'] not in self.allowed:continue
                key='@root' if component==design.rootComponent else component.entityToken
                claim=c.execute('SELECT issue_id FROM authoring_claims WHERE document_id=? AND component_id=?',(document_id,key)).fetchone()
                if claim and claim['issue_id']!=self.issue:
                    other=c.execute('SELECT record FROM authoring_issues WHERE issue_id=?',(claim['issue_id'],)).fetchone()
                    if other and (json.loads(other[0]).get('blocked') or json.loads(other[0]).get('active_operation')):
                        raise ValueError('Affected source has unresolved issue '+claim['issue_id']+'; changing job/agent/issue names cannot clear its budget')
            old=c.execute('SELECT record FROM authoring_issues WHERE issue_id=?',(self.issue,)).fetchone()
            r=json.loads(old[0]) if old else {'attempts':0,'elapsed_seconds':0,'growth':{'features':0,'sketches':0},
                'baseline':{i:{k:[e.entityToken for e in objects] for k,objects in cols.items()} for i,cols in self.before.items()},
                'baseline_id':self.task['baseline_id'],'history':[]}
            if r.get('active_operation'):raise ValueError('Previous issue attempt has uncertain effects; reconcile it before changing strategy')
            if r.get('blocked') and r.get('strategy_revision')==p['strategy_revision']:
                raise ValueError('Issue blocked: declare a coherent changed strategy; unchanged retry rejected')
            if r['attempts']>=p['max_attempts'] or r['elapsed_seconds']>=p['max_seconds']:raise ValueError('Adopted issue attempt/time budget exhausted; a new job/agent does not reset it')
            for kind in ('features','sketches'):
                if r['growth'][kind]+p['max_new_'+kind]>p['cumulative_new_'+kind]:raise ValueError('Planned additions exceed remaining cumulative '+kind+' budget')
            job=c.execute('SELECT job_id FROM jobs WHERE operation_id=?',(operation_id,)).fetchone()
            r.update(attempts=r['attempts']+1,active_operation=operation_id,active_job_id=job['job_id'] if job else None,
                     document_id=document_id,attempt_snapshot=attempt_snapshot,attempt_task=self.task,
                     attempt_started_at=time.time(),interrupted_at=None,
                     blocked=False,strategy_revision=p['strategy_revision'],policy=p)
            c.execute('INSERT OR REPLACE INTO authoring_issues VALUES(?,?)',(self.issue,canonical(r)))
            for m,component in selection.entries:
                if m['id'] in self.allowed:c.execute('INSERT OR REPLACE INTO authoring_claims VALUES(?,?,?)',(document_id,'@root' if component==design.rootComponent else component.entityToken,self.issue))
        self.record=r;self.started=time.monotonic()
        self.status={'status':'in_progress','issue_id':self.issue,'attempt':r['attempts'],
                     'enforcement':'preflight_budget_and_posthoc_growth' if path=='trusted_python' else 'narrow_preflight_and_postconditions',
                     'arbitrary_python_pre_dispatch_enforced':False}
    def remaining_seconds(self):
        return self.policy['max_seconds']-self.record['elapsed_seconds']-(time.monotonic()-self.started) if self.record else None
    def finish(self,execution_completed):
        if not self.record:return self.status
        after=counts(self.selection,self.allowed);growth={};removed={}
        for kind in ('features','sketches'):
            growth[kind]=sum(sum(not any(e==old for old in v[kind]) for e in after.get(i,{}).get(kind,[])) for i,v in self.before.items())
            removed[kind]=sum(sum(not any(e==now for now in after.get(i,{}).get(kind,[])) for e in v[kind]) for i,v in self.before.items())
        violations=[kind+'_growth' for kind in growth if growth[kind]>self.policy['max_new_'+kind]]
        if any(removed.values()):violations.append('history_removed_requires_separate_isolated_rebuild_review')
        if any(not getattr(e,'isValid',False) for e in self.sources):violations.append('source_feature_lost')
        elapsed=time.monotonic()-self.started;r=self.record;r['elapsed_seconds']+=elapsed
        for kind in growth:
            r['growth'][kind]+=growth[kind]
            if r['growth'][kind]>self.policy['cumulative_new_'+kind]:violations.append('cumulative_'+kind)
        if r['elapsed_seconds']>self.policy['max_seconds']:violations.append('issue_time_budget')
        r['blocked']=bool(violations) or not execution_completed;r['active_operation']=None
        attempt={'operation_id':self.operation_id,'growth':growth,'removed':removed,'elapsed_seconds':elapsed,
                 'violations':violations,'execution_completed':execution_completed,'strategy_revision':self.policy['strategy_revision']}
        r['history'].append(attempt)
        with self.store.connect() as c:c.execute('UPDATE authoring_issues SET record=? WHERE issue_id=?',(canonical(r),self.issue))
        self.status.update(status='fail' if violations else 'unproven' if not execution_completed else 'pass',
                           growth=growth,removed=removed,cumulative_growth=r['growth'],violations=violations,
                           elapsed_seconds=r['elapsed_seconds'],blocked=r['blocked'],
                           limitation='Counts and source retention only. Native parametric behavior, aesthetic simplicity and isolated replacement promotion need separate evidence.')
        return self.status
