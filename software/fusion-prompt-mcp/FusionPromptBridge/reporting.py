"""Compact wire responses with immutable, hash-addressed detail. No Autodesk imports."""
import hashlib
import json
import re
import tempfile
import os
from .job_store import canonical


def publish(store,payload):
    data=canonical(payload).encode();ident=hashlib.sha256(data).hexdigest()
    folder=store.root/'reports';folder.mkdir(exist_ok=True)
    path=folder/(ident+'.json')
    if not path.exists():
        with tempfile.NamedTemporaryFile(dir=folder,delete=False) as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno());temporary=stream.name
        os.replace(temporary,path)
    return {'report_id':ident,'sha256':ident,'bytes':len(data),'immutable':True}


def read(store,ident):
    if not re.fullmatch('[a-f0-9]{64}',ident):raise ValueError('Invalid report_id')
    data=(store.root/'reports'/(ident+'.json')).read_bytes()
    if hashlib.sha256(data).hexdigest()!=ident:raise ValueError('Report hash changed')
    return json.loads(data)


def measured(response,full_bytes):
    response['telemetry']={'detail_bytes':full_bytes,'response_bytes':0}
    for _ in range(6):
        size=len(canonical(response).encode())
        if size==response['telemetry']['response_bytes']:break
        response['telemetry']['response_bytes']=size
    return response


def summary(payload):
    result=payload.get('result') if isinstance(payload.get('result'),dict) else payload
    out={k:payload[k] for k in ('job_id','operation_id','status','progress','updated','cancel_requested') if k in payload}
    for k in ('document_id','design_id','edit_token','writer_id','cloud_complete','uncertain','execution_status',
              'regeneration_performed','approval_status','reconciliation_required'):
        if k in result:out[k]=result[k]
        elif k in payload:out[k]=payload[k]
    if result.get('file'):out['file']={k:result['file'][k] for k in ('id','version_id','version','complete') if k in result['file']}
    out['outcomes']={k:result['outcomes'][k] for k in ('execution','mutation','regeneration','integrity','edit_boundary','evidence',
        'export','presentation','engineering','authoring','readiness','approval') if k in result.get('outcomes',{})}
    for k in ('authoring','engineering'):
        if isinstance(result.get(k),dict):out[k+'_status']=result[k].get('status','unproven')
    out['replay_permitted']=False
    out['counts']={k:len(result[k]) for k in ('parameters','components','references','created','created_detected',
                    'warnings','files','checkpoints','stages') if isinstance(result.get(k),(list,dict))}
    if isinstance(result.get('measurements'),dict):out['counts']['measurements']=len(result['measurements'])
    validation=result.get('validation') or {};boundary=result.get('edit_boundary') or {}
    changed=boundary.get('changed_member_ids',[])
    out['counts']['changed_members']=len(changed)
    out['changed_member_ids']=[str(x)[:256] for x in changed[:8]]
    out['changed_members_omitted']=max(0,len(changed)-8)
    for k in ('feature_errors','inspection_gaps','evidence_gaps'):
        out['counts'][k]=len(validation.get(k,[]))
    out['counts']['boundary_violations']=len(boundary.get('violations',[]))
    out['validation_status']=validation.get('validation_status','not_checked')
    out['evidence_status']=validation.get('evidence_status','not_checked')
    blockers=boundary.get('violations',[])+validation.get('feature_errors',[])+validation.get('inspection_gaps',[])+validation.get('evidence_gaps',[])
    blockers += [{'kind':'authoring','reason':r} for r in result.get('authoring',{}).get('violations',[])]
    out['blockers']=[{k:str(row[k])[:240] for k in ('kind','id','check','name','reason','message') if k in row} for row in blockers[:8]]
    out['blocker_count']=len(blockers);out['blockers_omitted']=max(0,len(blockers)-8)
    if result.get('message'):out['message']=str(result['message'])[:512]
    if result.get('engineering_report'):
        engineering=result['engineering_report']['summary']
        out['engineering_detail_available']=True;out['engineering_conclusions']=engineering['conclusions']
        out['counts']['engineering_failed']=len(engineering.get('failed',[]))
        out['counts']['engineering_unproven']=len(engineering.get('unproven',[]))
        out['not_checked']=engineering.get('not_checked',[])[:12]
    reconciliation=payload.get('reconciliation') or result.get('reconciliation')
    if reconciliation:out['reconciliation']={k:reconciliation[k] for k in ('original_status','replayed','confirmation_status') if k in reconciliation}
    out['details_omitted']=True
    out['next_action']='Reconcile completed work and retrieve blockers; do not replay' if out.get('status') in ('failed','interrupted','cancelled') or out['blocker_count'] else 'Read declared conclusions; retrieve only needed evidence'
    out['omission_note']='Inventories, findings, values and receipts are retained in the immutable report; counts are not a pass.'
    return out


def response(store,payload,section='summary',after_revision='',offset=0,limit=50):
    ref=publish(store,payload)
    if after_revision==ref['report_id']:
        return measured({'unchanged':True,'detail':ref},ref['bytes'])
    if section=='full':return payload
    if section!='summary':return page(store,ref['report_id'],section,offset,limit)
    return measured(dict(summary(payload),detail=ref,revision=ref['report_id']),ref['bytes'])


def page(store,ident,section='raw',offset=0,limit=50,baseline_report_id=''):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=32768:
        raise ValueError('Use offset>=0 and 1..32768 limit; structured pages limited to 100 rows')
    payload=read(store,ident);raw=canonical(payload)
    if section=='raw':
        total=len(raw);value=raw[offset:offset+limit]
        out={'encoding':'canonical JSON UTF-8; cursor counts characters','text':value,'total':total}
    else:
        if section=='delta':
            if not baseline_report_id:raise ValueError('delta requires baseline_report_id')
            old=read(store,baseline_report_id)
            if old.get('document_id')!=payload.get('document_id') or not payload.get('document_id'):
                raise ValueError('Parameter deltas require matching document snapshots')
            a=dict(old.get('parameters',[]));b=dict(payload.get('parameters',[]))
            value=[{'name':n,'before':a.get(n),'after':b.get(n)} for n in sorted(a.keys()|b.keys()) if a.get(n)!=b.get(n)]
        else:
            value=payload
            for key in section.strip('/').split('/'):
                value=value[int(key)] if isinstance(value,list) else value[key.replace('~1','/').replace('~0','~')]
        if not isinstance(value,(list,dict)):value=[value]
        if isinstance(value,dict):value=list(value.items())
        limit=min(limit,100);total=len(value);items=[]
        for i,item in enumerate(value[offset:offset+limit],offset):
            if len(canonical(item).encode())>8192:
                item={'detail_omitted':True,'index':i,'reason':'Entry exceeds 8192 bytes; retrieve /subsection or raw pages'}
            items.append(item)
        out={'items':items,'total':total}
    out.update(report_id=ident,sha256=ident,section=section,offset=offset,next_offset=offset+limit if offset+limit<total else None)
    return measured(out,len(raw.encode()))
