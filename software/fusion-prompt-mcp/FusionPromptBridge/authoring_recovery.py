"""Native-observed ledger reconciliation. No geometry repair, approval or callback replay."""
import hashlib
import json
import time
from . import advanced, model_tools, scope, preservation
from .job_store import canonical


def key(design,component):
    return '@root' if component==design.rootComponent else component.entityToken


def snapshot(design,selection,task):
    allowed=set(task['allowed_member_ids']);members=[];components=[]
    for component in scope.live_components(design):
        member=selection.member(component)
        components.append({'token':key(design,component),'revision':component.revisionId,
                           'permitted':bool(member and member['id'] in allowed)})
        if member and member['id'] in allowed:
            members.append({'token':key(design,component),'id':member['id'],
                            **{name:[e.entityToken for e in model_tools.each(getattr(component,name))]
                               for name in ('features','sketches')}})
    return {'components':components,'members':members,
            'parameters':{p.name:p.expression for p in model_tools.each(design.allParameters)},
            'occurrences':[{'token':o.entityToken,'component':key(design,o.component),'matrix':list(o.transform2.asArray())}
                           for o in model_tools.each(design.rootComponent.allOccurrences)]}


def resolve(design,token):
    return design.rootComponent if token=='@root' else advanced.resolve(design,token)


def inspect(ctx,issue_id,original_job_id=''):
    ctx.guard()
    with ctx.store.connect() as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='authoring_issues'").fetchone():
            raise ValueError('Unknown authoring issue; no authoring ledger exists')
        row=db.execute('SELECT record FROM authoring_issues WHERE issue_id=?',(issue_id,)).fetchone()
    if not row:raise ValueError('Unknown authoring issue')
    record=json.loads(row[0]);blockers=[]
    if not record.get('active_operation'):raise ValueError('Issue has no interrupted active attempt to acknowledge')
    if not record.get('attempt_snapshot') or not record.get('attempt_task'):
        raise ValueError('Legacy ledger lacks durable attempt baseline; automatic acknowledgement unavailable')
    document=getattr(getattr(ctx.document,'dataFile',None),'id',None) or ctx.request['document_id']
    if document!=record['document_id']:raise ValueError('Authoring reconciliation belongs to another document/file; unsaved cross-session identity cannot be inferred')
    ident=record.get('active_job_id')
    if ident:
        if original_job_id!=ident:raise ValueError('Supply the exact original_job_id from the active ledger')
        job=ctx.store.result(ident)
        if job['operation_id']!=record['active_operation'] or job['status'] not in ('interrupted','failed','cancelled'):
            raise ValueError('Original operation is not an unsuccessful terminal job; wait or reconcile its actual state')
        ended=job['updated']
    else:
        if original_job_id or not record.get('interrupted_at'):
            raise ValueError('Narrow attempt requires exclusive bridge restart recovery before acknowledgement')
        ended=record['interrupted_at']
    task=record['attempt_task'];before=record['attempt_snapshot']
    if not ctx.selection or ctx.selection.legacy:raise ValueError('Explicit current scope required for ledger reconciliation')
    for member in before['members']:
        component=resolve(ctx.design,member['token']);current=ctx.selection.member(component)
        if not current or current['id'] not in ctx.selection.target_ids:
            raise ValueError('Reconciliation scope must target every original permitted member')
    now=snapshot(ctx.design,ctx.selection,dict(task,allowed_member_ids=[
        ctx.selection.member(resolve(ctx.design,m['token']))['id'] for m in before['members']]))
    live=scope.live_components(ctx.design);old_components=[]
    for old in before['components']:
        try:
            component=resolve(ctx.design,old['token']);old_components.append(component)
            if not any(component==c for c in live):raise ValueError('Component no longer occurs')
            if not old['permitted'] and component.revisionId!=old['revision']:blockers.append('protected_component_changed:'+old['token'])
        except Exception:blockers.append('missing_component:'+old['token'])
    if any(not any(c==old for old in old_components) for c in live):blockers.append('new_component_definition')
    growth={'features':0,'sketches':0};removed={'features':0,'sketches':0}
    for member in before['members']:
        component=resolve(ctx.design,member['token'])
        for kind in growth:
            current=model_tools.each(getattr(component,kind));retained=[]
            for token in member[kind]:
                try:
                    entity=resolve(ctx.design,token)
                    if not getattr(entity,'isValid',False) or not any(entity==e for e in current):raise ValueError('History missing')
                    retained.append(entity)
                except Exception:removed[kind]+=1
            growth[kind]+=sum(not any(e==old for old in retained) for e in current)
    if any(removed.values()):blockers.append('history_removed_or_unresolvable')
    for token in record['policy']['source_feature_tokens']:
        try:
            if not getattr(resolve(ctx.design,token),'isValid',False):raise ValueError('Source lost')
        except Exception:blockers.append('source_feature_lost')
    allowed_parameters=set(task.get('allowed_parameter_names',[]))
    parameters={p.name:p for p in model_tools.each(ctx.design.allParameters)}
    for name in before['parameters'].keys()|now['parameters'].keys():
        if before['parameters'].get(name)==now['parameters'].get(name) or name in allowed_parameters:continue
        owner=preservation.generated_owner(parameters[name]) if name not in before['parameters'] and name in parameters else None
        if not owner or not any(owner==resolve(ctx.design,m['token']) for m in before['members']):
            blockers.append('foreign_parameter_change:'+name)
    occurrences=model_tools.each(ctx.design.rootComponent.allOccurrences)
    permitted=[resolve(ctx.design,m['token']) for m in before['members']]
    retained_occurrences=[]
    for old in before['occurrences']:
        try:
            occurrence=resolve(ctx.design,old['token']);retained_occurrences.append(occurrence)
            if (not any(occurrence==o for o in occurrences) or preservation.placement_changed(old['matrix'],occurrence.transform2.asArray())) and not any(occurrence.component==c for c in permitted):
                blockers.append('protected_occurrence_changed')
        except Exception:blockers.append('missing_occurrence')
    if any(not any(o==old for old in retained_occurrences) and not any(o.component==c for c in permitted) for o in occurrences):
        blockers.append('foreign_occurrence_added')
    elapsed=max(0,ended-record['attempt_started_at'])
    if ended<record['attempt_started_at']:blockers.append('invalid_attempt_clock')
    proposal={'issue_id':issue_id,'original_job_id':ident,'operation_id':record['active_operation'],
              'ledger_sha256':hashlib.sha256(row[0].encode()).hexdigest(),
              'growth':growth,'removed':removed,'charged_seconds':elapsed,'blockers':sorted(set(blockers)),
              'attempts':record['attempts'],'cumulative_growth':{k:record['growth'][k]+growth[k] for k in growth},
              'elapsed_seconds':record['elapsed_seconds']+elapsed,'replayed':False,
              'qualification':'Ledger accounting only; no geometry/health/approval promotion. Changed strategy and remaining adopted budget required.'}
    observation={'record':record,'current':now,'proposal':proposal}
    proposal['observation_id']=hashlib.sha256(canonical(observation).encode()).hexdigest()
    return proposal


def acknowledge(ctx,issue_id,observation_id,note,original_job_id=''):
    if ctx.request.get('mode')!='reconcile':raise ValueError('Acknowledgement requires restricted reconcile mode and a current writer token')
    if not isinstance(note,str) or not note.strip():raise ValueError('Explicit reconciliation note required')
    proposal=inspect(ctx,issue_id,original_job_id)
    if proposal['observation_id']!=observation_id:raise ValueError('Stale authoring observation; inspect actual state again')
    if proposal['blockers']:raise ValueError('Authoring reconciliation blocked: '+','.join(proposal['blockers']))
    with ctx.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT record FROM authoring_issues WHERE issue_id=?',(issue_id,)).fetchone()
        record=json.loads(row[0])
        if hashlib.sha256(row[0].encode()).hexdigest()!=proposal['ledger_sha256']:raise ValueError('Authoring ledger changed during acknowledgement')
        record['growth']=proposal['cumulative_growth'];record['elapsed_seconds']=proposal['elapsed_seconds']
        record['history'].append(dict(proposal,note=note,execution_completed=False,acknowledged_at=time.time()))
        record.update(active_operation=None,active_job_id=None,blocked=True)
        db.execute('UPDATE authoring_issues SET record=? WHERE issue_id=?',(canonical(record),issue_id))
    return dict(proposal,status='acknowledged_not_qualified',blocked=True,changed_strategy_required=True,
                original_status_preserved=True,geometry_modified=False)
