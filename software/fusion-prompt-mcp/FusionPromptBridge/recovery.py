"""Durable stage observations and read-only edit reconciliation; never replay callbacks."""
import json
import time
import traceback
from . import engineering, model_tools, verification
from .design_intent import ReferenceFailure


def observe(ctx):
    components=[]
    for c in model_tools.each(ctx.design.allComponents):
        components.append({'token':c.entityToken,'revision':c.revisionId})
    occurrences=[{'token':o.entityToken,'component':o.component.entityToken,'transform_cm':o.transform2.asArray()}
                 for o in model_tools.each(ctx.design.rootComponent.allOccurrences)]
    file=ctx.document.dataFile if ctx.document.isSaved else None
    return {'document_id':ctx.request['document_id'],'cloud_file_id':file.id if file else None,
            'cloud_version':file.versionNumber if file else None,'modified':ctx.document.isModified,
            'components':components,'occurrences':occurrences,
            'parameters':{p.name:p.expression for p in model_tools.each(ctx.design.allParameters)}}


def changes(before,after):
    if not before or not after:return {'model_changed':None,'status':'unproven','reason':'Missing before/after observation'}
    fields=[k for k in ('components','occurrences','parameters','modified','cloud_version') if before[k]!=after[k]]
    return {'model_changed':bool(fields),'changed_fields':fields,
            'status':'observed','limitation':'Revision/placement/parameter evidence; change-then-restore and external side effects are not detected.'}


def run_stage(ctx,stage_id,action,postcondition,protected_plan=None):
    if ctx.read_only:raise ValueError('Stages require modeling mode')
    if not stage_id or not callable(action) or not callable(postcondition):raise ValueError('Named stage/action/postcondition required')
    stages=ctx.result.setdefault('stages',{})
    if stage_id in stages:raise ValueError('Stage already attempted; reconcile original result rather than replay it')
    ctx.check_cancel()
    protected=engineering.Session(ctx,protected_plan).protected() if protected_plan else {}
    if protected_plan and (not protected or any('signature' not in r for r in protected.values())):
        raise ValueError('Protected stage requires resolvable protected interfaces before mutation')
    row={'status':'preparing','before':observe(ctx),'protected_before':protected,
         'protected_plan':protected_plan,'started':time.time(),'replayed':False}
    stages[stage_id]=row;ctx.flush()
    # Completed checkpoint before action; a checkpoint failure cannot run the callback.
    row['checkpoint']=ctx.checkpoint('stage_'+stage_id)
    row['status']='started';ctx.flush();begin=time.perf_counter()
    try:
        value=action(ctx);json.dumps(value,allow_nan=False)
        row['action_returned']=True;row['action_result']=value;ctx.flush();ctx.synchronize()
        post=postcondition(ctx);json.dumps(post,allow_nan=False)
        row['postcondition']=post
        if not isinstance(post,dict) or post.get('status')!='pass':raise RuntimeError('Stage postcondition not proven')
        if protected_plan:
            row['protected_after']=engineering.Session(ctx,protected_plan).protected()
            row['protected_comparison']=engineering.compare_protected(protected,row['protected_after'])
            if row['protected_comparison']['status']!='pass':raise RuntimeError('Protected interface metrics changed or unavailable')
        row.update(status='completed',return_value=value)
        return value
    except BaseException as exc:
        row.update(status='failed',error=str(exc),error_code=getattr(exc,'code','stage_failure'),traceback=traceback.format_exc())
        raise
    finally:
        row['duration_seconds']=time.perf_counter()-begin
        try:row['after']=observe(ctx);row['change_observation']=changes(row['before'],row['after'])
        except Exception as exc:row['change_observation']={'model_changed':None,'status':'unproven','reason':str(exc)}
        ctx.flush()


def reconcile(ctx,job_id):
    """Only inspect original state/checkpoints. No old source or action is executed."""
    ctx.check_cancel();job=ctx.store.result(job_id)
    if job['status'] not in ('failed','cancelled','interrupted'):raise ValueError('Reconcile only unsuccessful terminal jobs')
    old=job.get('result') or {};now=observe(ctx);before=old.get('before_observation')
    if not before:raise ValueError('Original job lacks durable baseline; inspect its checkpoint manually')
    same_doc=before['document_id']==now['document_id']
    same_file=before.get('cloud_file_id') and before['cloud_file_id']==now.get('cloud_file_id')
    if not same_doc and not same_file:
        raise ReferenceFailure('wrong_document','Unsaved/new-session identity cannot be inferred; locate original cloud file or inspect checkpoint manually')
    protected=[];states=old.get('stages',{})
    for ident,row in states.items():
        plan=row.get('protected_plan')
        if plan:
            plan=dict(plan,document_id=ctx.request['document_id'])
            try:report=engineering.compare_protected(row['protected_before'],engineering.Session(ctx,plan).protected())
            except Exception as exc:report={'status':'unproven','blocker':str(exc)}
            protected.append({'stage':ident,**report})
    completed=[ident for ident,row in states.items() if row['status']=='completed']
    unresolved=[ident for ident,row in states.items() if row['status']!='completed']
    return {'job_id':job_id,'original_status':job['status'],'replayed':False,'automatic_resume':False,
            'completed_stages_do_not_replay':completed,'unresolved_stages':unresolved,
            'change_observation':changes(before,now),
            'since_last_observation':changes(old.get('after_observation'),now),
            'protected_interfaces':protected,'checkpoints':old.get('checkpoints',[]),
            'next_action':'Preserve completed stages. For unresolved stages inspect stated postconditions/checkpoint; submit only a separately scoped corrective operation with a new hypothesis and original job linkage.',
            'blocker':'No stage records; completion boundary cannot be inferred' if not states else
                      'Protected evidence failed or unavailable' if any(r['status']!='pass' for r in protected) else
                      'Interrupted action outcome requires inspection' if unresolved else None,
            'approval_status':'not_evaluated'}
