"""Cloud workflow. Every function touching Autodesk objects runs on the UI thread.
No deletes, silent reloads, link replacement, or automatic recovery replay.
"""
import hashlib
import json
import math
import time
import traceback
import uuid
import adsk.core
import adsk.fusion
from . import advanced

_pending = {}
_tokens = {}

def each(collection):
    return [collection.item(i) for i in range(collection.count)]

def named(value):
    return {'id': value.id, 'name': value.name}

def required(value, label):
    if not value: raise ValueError(label + ' not found or inaccessible')
    return value

def file_info(file, refresh=True):
    if refresh and not file.refresh(None): raise RuntimeError('Fusion cloud metadata refresh failed')
    return dict(named(file), version_id=file.versionId, version=file.versionNumber,
                latest_version=file.latestVersionNumber, complete=file.isComplete,
                read_only=file.isReadOnly, in_use=file.isInUse,
                project_id=file.parentProject.id, folder_id=file.parentFolder.id)

def snapshot(app, design, document_id):
    doc = app.activeDocument
    refs = []
    for ref in each(doc.allDocumentReferences):
        info = file_info(ref.dataFile)
        linked = ref.referencedDocument
        refs.append(dict(info, referenced_version=ref.version, out_of_date=ref.isOutOfDate,
                         open_document_modified=bool(linked and linked.isModified)))
    return {'document_id': document_id, 'name': doc.name, 'modified': doc.isModified,
            'file': file_info(doc.dataFile) if doc.isSaved else None,
            'references': sorted(refs, key=lambda r: (r['id'], r['referenced_version'])),
            'components': [(c.name, c.revisionId) for c in each(design.allComponents)],
            'parameters': [(p.name, p.expression) for p in each(design.allParameters)]}

def digest_state(state, pins):
    value=json.loads(json.dumps(state))
    for ref in value['references']:
        if pins.get(ref['id'])==ref['referenced_version']:
            # A new AVAILABLE version does not alter an explicitly accepted dependency.
            ref.pop('latest_version',None);ref.pop('out_of_date',None)
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

def inspect_state(app, design, document_id, acquire=True, writer_id='legacy', accepted_reference_versions=None):
    state=snapshot(app,design,document_id)
    result=dict(state,guard_scope='Optimistic pre-operation check, not a distributed lock or Python sandbox')
    if not acquire:return result
    if not isinstance(writer_id,str) or not writer_id.strip():raise ValueError('writer_id required')
    pins=accepted_reference_versions or {}
    if not isinstance(pins,dict) or any(not isinstance(k,str) or type(v) is not int or v<1 for k,v in pins.items()):
        raise ValueError('accepted_reference_versions maps file IDs to positive version numbers')
    actual={r['id']:r['referenced_version'] for r in state['references']}
    if any(r['id'] in pins and actual[r['id']]!=r['referenced_version'] for r in state['references']):
        raise ValueError('Mixed versions of one file require an explicit subassembly workflow; file-level pin is ambiguous')
    if any(actual.get(k)!=v for k,v in pins.items()):raise ValueError('Accepted pin does not match current referenced version')
    digest=digest_state(state,pins);previous=_tokens.get(document_id)
    if previous and previous['writer_id']!=writer_id:
        raise ValueError('Another writer holds the token. Release it explicitly; observation does not take ownership.')
    if not previous or previous['digest']!=digest or previous['pins']!=pins:
        previous={'token':uuid.uuid4().hex,'digest':digest,'writer_id':writer_id,'pins':dict(pins)}
        _tokens[document_id]=previous
    return dict(result,edit_token=previous['token'],writer_id=writer_id,accepted_reference_versions=pins)

def release_token(document_id,token,writer_id):
    previous=_tokens.get(document_id)
    if not previous or previous['token']!=token or previous['writer_id']!=writer_id:
        raise ValueError('Writer/token mismatch')
    del _tokens[document_id]
    return {'released':True,'document_id':document_id,'writer_id':writer_id}

def require_edit(app, design, document_id, token, allow_stale_refs=False,
                 accepted_reference_versions=None, writer_id='legacy'):
    previous=_tokens.get(document_id)
    if not token or not previous or previous['token']!=token or previous['writer_id']!=writer_id:
        raise ValueError('Acquire a writer edit_token for this document and writer_id')
    pins=accepted_reference_versions or {}
    if pins!=previous['pins']:raise ValueError('Accepted reference pins differ from writer baseline')
    state=snapshot(app,design,document_id)
    if digest_state(state,pins)!=previous['digest']:
        raise ValueError('Document or relevant cloud versions changed since inspection. Reinspect and adapt to user edits.')
    file=state['file']
    if file and (file['version']!=file['latest_version'] or file['read_only'] or file['in_use'] or not file['complete']):
        raise ValueError('Target is stale, read-only, in use by another user, or still processing. Historical inspection does not authorize overwriting latest.')
    for ref in state['references']:
        if ref['open_document_modified'] or not ref['complete']:
            raise ValueError('Referenced document has unsaved changes or pending cloud processing')
        if ref['out_of_date'] and not allow_stale_refs and pins.get(ref['id'])!=ref['referenced_version']:
            raise ValueError('References are out of date without an explicit accepted pin. Preserve exact versions or update deliberately.')
    del _tokens[document_id]
    return state

def cloud_checkpoint(app, design, document_id):
    state = snapshot(app, design, document_id)
    file = state['file']
    if state['modified'] or not file or not file['complete']:
        raise ValueError('Linked assembly checkpoint needs a completed cloud save. Save, poll, and reinspect first.')
    if file['version'] != file['latest_version']:
        raise ValueError('Cannot checkpoint a stale assembly')
    if any(r['open_document_modified'] or not r['complete'] for r in state['references']):
        raise ValueError('Save referenced documents before checkpointing the assembly')
    return {'kind': 'cloud_version', 'file': file, 'references': state['references'],
            'recovery': 'Open recorded version in Fusion for inspection. No automatic promotion or rollback.',
            'self_contained_archive': False}

def hub(app, ident):
    return required(app.data.dataHubs.itemById(ident), 'Hub')

def project(app, args):
    return required(hub(app, args['hub_id']).dataProjects.itemById(args['project_id']), 'Project')

def folder(app, args):
    root = project(app, args).rootFolder
    wanted = args['folder_id']
    queue = [root]
    while queue:
        node = queue.pop()
        if node.id == wanted: return node
        queue.extend(each(node.dataFolders))
    raise ValueError('Folder does not belong to the selected project')

def browse(app, args):
    if not args.get('hub_id'): return {'hubs': [named(h) for h in each(app.data.dataHubs)]}
    if not args.get('project_id'):
        return {'projects': [dict(named(p), root_folder_id=p.rootFolder.id)
                             for p in each(hub(app,args['hub_id']).dataProjects)]}
    target = folder(app,args) if args.get('folder_id') else project(app,args).rootFolder
    return {'folder': named(target), 'folders': [named(f) for f in each(target.dataFolders)],
            'files': [file_info(f, False) for f in each(target.dataFiles)]}

def ensure_named(collection, name):
    if not isinstance(name,str) or not name.strip(): raise ValueError('Use a descriptive nonempty name')
    matches = [x for x in each(collection) if x.name.casefold() == name.casefold()]
    if len(matches)>1: raise ValueError('Ambiguous name; select an existing ID')
    return matches[0] if matches else required(collection.add(name), 'Created item')

def destination(app, args):
    target = folder(app,args)
    name = args['name']
    if not isinstance(name,str) or not name.strip(): raise ValueError('Name is required')
    if any(f.name.casefold()==name.casefold() for f in each(target.dataFiles)):
        raise ValueError('File name already exists. Open its stable ID and save a new version; do not create a duplicate.')
    return target

def get_file(app, args):
    # Autodesk findFileById documents a version URN; browse returns version_id.
    f = required(app.data.findFileById(args['version_id']), 'File version')
    if not f.refresh(None): raise RuntimeError('Fusion cloud metadata refresh failed')
    if f.versionNumber != args['expected_version'] or not f.isComplete:
        raise ValueError('Requested version mismatch or file still processing')
    if f.latestVersionNumber != args['expected_version'] and not args.get('allow_historical',False):
        raise ValueError('A newer cloud version exists. Reinspect before opening/inserting.')
    return f

def start(store, job, app, design_getter, document_id_getter):
    request = job['request']; action = request['action']; args = request['arguments']; ident=job['job_id']
    result = {'action': action, 'cloud_complete': False, 'partial_changes_possible': False, 'uncertain':False, 'approval_status':'not_evaluated'}
    try:
        from .compatibility import require_match
        require_match(request.get('_caller'))
        store.assert_no_uncertain_cloud(exclude_job_id=ident)
        if _pending: raise ValueError('A cloud upload is pending. Poll it before another cloud operation.')
        store.partial(ident,result)
        if action == 'ensure_project':
            p = ensure_named(hub(app,args['hub_id']).dataProjects,args['name'])
            result['project'] = dict(named(p),root_folder_id=p.rootFolder.id)
            store.partial(ident,result)
            result['folders'] = {}
            for name in ('Assembly','Parts','Purchased Components'):
                result['folders'][name] = named(ensure_named(p.rootFolder.dataFolders,name))
                store.partial(ident,result)
        elif action == 'ensure_folder':
            result['folder'] = named(ensure_named(folder(app,args).dataFolders,args['name']))
        elif action == 'open':
            f = get_file(app,args)
            for doc in each(app.documents):
                if doc.isSaved and doc.dataFile.id == f.id:
                    if doc.isModified or doc.dataFile.versionNumber != f.versionNumber:
                        raise ValueError('File already open with unsaved changes or another version. Preserve it and resolve manually.')
                    if not doc.activate(): raise RuntimeError('Could not activate the selected document')
                    break
            else:
                opened=required(app.documents.open(f,True), 'Opened document')
                if not opened.activate(): raise RuntimeError('Could not activate the opened document')
            result.update(file=file_info(f), document_id=document_id_getter(),
                          historical_inspection=f.versionNumber!=f.latestVersionNumber)
        else:
            doc_id = args['document_id']
            if document_id_getter() != doc_id: raise ValueError('Active document changed')
            design = design_getter(); doc=app.activeDocument
            state = require_edit(app,design,doc_id,args['edit_token'],action=='update_reference',
                                 args.get('accepted_reference_versions'),args.get('writer_id','legacy'))
            result['before'] = state
            result['task_link']=args.get('task_link')
            store.partial(ident,result)
            if action in ('save','save_component'):
                baseline = doc.dataFile.versionNumber if doc.isSaved else 0
                result['save_intent']={'document_id':doc_id,'before_file':state['file'],
                                       'expected_version':baseline+1 if action=='save' else 1,
                                       'references':state['references'],'name':args.get('name',doc.name)}
                if action == 'save':
                    if doc.isSaved:
                        if any(args.get(k) for k in ('name','folder_id','project_id','hub_id')):
                            raise ValueError('Existing files save in place. Omit destination/name; identity must be preserved.')
                        if not doc.isModified:
                            result.update(file=file_info(doc.dataFile),cloud_complete=True)
                            store.finish(ident,'succeeded',result); return
                        result['uncertain']=True;store.partial(ident,result)
                        ok = doc.save(args.get('description','MCP shared-edit checkpoint'))
                    else:
                        target=destination(app,args)
                        result['save_intent'].update(folder_id=target.id,project_id=args.get('project_id'))
                        result['uncertain']=True;store.partial(ident,result)
                        ok=doc.saveAs(args['name'],target,args.get('description',''),'')
                    if not ok: raise RuntimeError('Fusion rejected save')
                    future=None
                else:
                    target=destination(app,args)
                    result['save_intent'].update(folder_id=target.id,project_id=args.get('project_id'))
                    component=advanced.resolve(design,args['component_token'],adsk.fusion.Component)
                    advanced.editable(design,component)
                    result['uncertain']=True;store.partial(ident,result)
                    future=required(component.saveCopyAs(args['name'],target,args.get('description',''),''),'Component save future')
                    result['source_component_token']=args['component_token']
                    result['note']='Independent native copy; existing occurrences and joints are NOT replaced. Open/edit this new file by ID.'
                result['partial_changes_possible']=True
                result['status_note']='Save started; cloud completion not yet confirmed'
                _pending[ident]={'app':app,'doc':doc,'future':future,'baseline':baseline,'result':result,'started':time.monotonic()}
                store.partial(ident,result); store.progress(ident,0.5,'Waiting for Fusion cloud processing'); return
            elif action == 'insert':
                f=get_file(app,args)
                if f.versionNumber!=f.latestVersionNumber and args.get('accepted_insert_version')!=f.versionNumber:
                    raise ValueError('Historical insertion needs accepted_insert_version matching the inspected version')
                if not doc.isSaved or doc.dataFile.parentProject.id!=f.parentProject.id:
                    raise ValueError('Linked insertion requires an assembly saved in the same project')
                if doc.dataFile.id==f.id: raise ValueError('Cannot insert a design into itself')
                result['checkpoint']=cloud_checkpoint(app,design,doc_id)
                store.partial(ident,result)
                values=args['transform_cm']
                if not isinstance(values,list) or len(values)!=16 or any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
                    raise ValueError('transform_cm must contain 16 finite matrix values')
                transform=adsk.core.Matrix3D.create()
                if not transform.setWithArray(values): raise ValueError('Invalid transform')
                occurrence=required(design.rootComponent.occurrences.addByInsert(f,transform,True),'Linked occurrence')
                result['occurrence']=advanced.ref(occurrence)
                result['file']=file_info(f)
            elif action == 'update_reference':
                result['checkpoint']=cloud_checkpoint(app,design,doc_id)
                store.partial(ident,result)
                matches=[r for r in each(doc.documentReferences) if r.dataFile.id==args['file_id']]
                if len(matches)!=1: raise ValueError('Select exactly one direct reference; edit nested subassembly in its own document')
                ref=matches[0]
                if ref.dataFile.latestVersionNumber != args['expected_latest_version']:
                    raise ValueError('Reference version changed since inspection')
                latest=file_info(ref.dataFile.latestVersion)
                if not latest['complete'] or latest['version']!=args['expected_latest_version']:
                    raise ValueError('Requested reference version is not fully processed')
                # Pin exact inspected version rather than racing getLatestVersion().
                ref.version=args['expected_latest_version']
                if ref.version!=args['expected_latest_version']: raise RuntimeError('Reference update failed')
                result['reference']=file_info(ref.dataFile)
            else: raise ValueError('Unsupported cloud action')
        result['cloud_complete']= action in ('ensure_project','ensure_folder','open')
        result['requires_save']=action in ('insert','update_reference')
        store.finish(ident,'succeeded',result)
    except Exception as exc:
        result.update(message=str(exc),traceback=traceback.format_exc(),partial_changes_possible=True)
        store.finish(ident,'failed',result)

def tick(store):
    """One poll per custom event, with no wait loop; the UI loop owns all futures/documents."""
    for ident,pending in list(_pending.items()):
        result=pending['result']
        try:
            if store.row(ident)['cancel_requested']:
                result.update(message='Stopped monitoring. Save may still complete; inspect before any retry.',partial_changes_possible=True)
                store.finish(ident,'cancelled',result); del _pending[ident]; continue
            if time.monotonic()-pending['started']>600:
                raise TimeoutError('Cloud save not confirmed after 10 minutes. Inspect Fusion; do not resubmit under a new ID.')
            future=pending['future']
            if future:
                state=future.uploadState
                if state==adsk.core.UploadStates.UploadFailed: raise RuntimeError('Fusion cloud upload failed')
                if state!=adsk.core.UploadStates.UploadFinished: continue
                file=future.dataFile
            else:
                file=pending['doc'].dataFile
                if not file or file.versionNumber<=pending['baseline']: continue
                if file.versionNumber!=pending['baseline']+1:
                    raise RuntimeError('Document version advanced unexpectedly during save. Inspect the version history.')
            if not file: continue
            # First save may temporarily expose local lineage / incomplete metadata.
            # Observe remote version resolution; never call save again from a poll.
            intent=result.get('save_intent',{})
            first_save=result.get('action')=='save' and not intent.get('before_file')
            try:
                info=file_info(file)
                if first_save:
                    remote=pending['app'].data.findFileById(info['version_id'])
                    if not remote:raise RuntimeError('Cloud version not yet resolvable')
                    confirmed=file_info(remote)
                    if (confirmed['id'],confirmed['version_id'])!=(info['id'],info['version_id']):
                        raise RuntimeError('Local and cloud identities not yet consistent')
                    info=confirmed
            except Exception as exc:
                if not first_save:raise
                result['metadata_wait']={'reason':str(exc),'elapsed_seconds':time.monotonic()-pending['started']}
                store.partial(ident,result);continue
            check_saved_identity(info,intent,result.get('action'))
            result['file']=info; store.partial(ident,result)
            if not info['complete']: continue
            result.update(cloud_complete=True,uncertain=False,status_note='Cloud version fully processed')
            store.finish(ident,'succeeded',result); del _pending[ident]
        except Exception as exc:
            result.update(message=str(exc),traceback=traceback.format_exc(),partial_changes_possible=True)
            store.finish(ident,'failed',result); del _pending[ident]

def reset():
    _pending.clear(); _tokens.clear()


def check_saved_identity(info,intent,action):
    before=intent.get('before_file')
    if info['version']!=intent.get('expected_version'):raise ValueError('Observed version differs from expected save outcome')
    if action=='save' and before and info['id']!=before['id']:raise ValueError('Observed file identity differs from original save target')
    if not before or action=='save_component':
        for field in ('name','folder_id','project_id'):
            if intent.get(field) and info.get(field)!=intent[field]:raise ValueError('Observed first-save destination differs: '+field)


def reconcile(store,app,job_id,version_id='',confirmation_note=''):
    """Observe a late save; acknowledgement is explicit caller evidence, never automatic replay."""
    row=store.result(job_id);result=row.get('result') or {}
    if not result.get('uncertain'):return dict(row,reconciliation_required=False)
    if row['status'] not in ('failed','cancelled','interrupted'):
        raise ValueError('Poll the running job; reconciliation is only for an uncertain terminal job')
    if not version_id:raise ValueError('Inspect original job/Fusion version history and provide the observed version_id')
    file=required(app.data.findFileById(version_id),'Observed cloud version')
    info=file_info(file);intent=result.get('save_intent',{});before=intent.get('before_file')
    if not info['complete']:raise ValueError('Observed cloud version still processing')
    check_saved_identity(info,intent,result.get('action'))
    report={'observed_file':info,'association':'caller must confirm this version contains the intended edits',
            'original_status':row['status'],'replayed':False}
    if confirmation_note.strip():
        report.update(confirmation_note=confirmation_note,confirmation_status='caller_reported_not_authenticated')
        result.update(uncertain=False,reconciliation=report)
        store.annotate_result(job_id,result)
        row=store.result(job_id)
    return dict(row,reconciliation=report,reconciliation_required=not bool(confirmation_note.strip()))
