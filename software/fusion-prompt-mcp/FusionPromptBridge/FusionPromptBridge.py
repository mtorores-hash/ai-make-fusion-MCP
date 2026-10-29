"""Fusion add-in. All adsk model calls execute in CustomEventHandler on the UI thread."""
import json
import math
import os
from pathlib import Path
import threading
import time
import uuid
import adsk.core
import adsk.fusion
from . import advanced, model_tools, batch_runner, cloud, reporting, maintainability
from . import scope as scopes
from .job_store import Store, BridgeLock
from . import compatibility

ROOT = Path.home() / '.fusion-prompt-mcp'
EVENT_ID = 'ai.make.fusion.prompt.v01'
_store = _lock = None
_busy = False
_owner = uuid.uuid4().hex
_app = _event = _handler = _thread = None
_stop = threading.Event()
_documents = []
ALLOWED = {'browse_cloud','document_state','acquire_edit_token','release_edit_token','reconcile_cloud_job'} | {'inspect', 'new_design', 'rectangle', 'circle', 'extrude', 'parameter', 'export'} | advanced.OPS | {'inspect_full', 'select_geometry', 'measure_distance', 'check_interference', 'validate_model', 'audit_hygiene'}

def atomic_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, allow_nan=False), encoding='utf-8')
    os.replace(temp, path)

def design_id():
    doc = _app.activeDocument
    if not doc:
        return None
    for previous, ident in _documents:
        if previous.isValid and previous == doc:
            return ident
    ident = uuid.uuid4().hex
    _documents.append((doc, ident))
    return ident

def design():
    d = adsk.fusion.Design.cast(_app.activeProduct)
    if not d:
        raise ValueError('Activate a Fusion Design document.')
    return d

def items(collection):
    return [collection.item(i) for i in range(collection.count)]

def ref(entity):
    return {'name': entity.name, 'token': entity.entityToken}

def inspect():
    d = design()
    root = d.rootComponent
    bodies = []
    for body in items(root.bRepBodies):
        box = body.boundingBox
        bodies.append(dict(ref(body), size_mm=[10 * (getattr(box.maxPoint, a) -
                           getattr(box.minPoint, a)) for a in ('x','y','z')]))
    return {'design_id': design_id(), 'document': _app.activeDocument.name,
            'version': '0.8.0', 'root_component': ref(root), 'scope': 'root summary; use inspect_assembly for components', 'bodies': bodies,
            'sketches': [dict(ref(s), profiles=s.profiles.count) for s in items(root.sketches)],
            'parameters': [{'name': p.name, 'expression': p.expression, 'unit': p.unit}
                           for p in items(d.allParameters)],
            'features': [{'name': f.name, 'health': str(f.healthState),
                          'message': f.errorOrWarningMessage} for f in items(root.features)]}

def number(args, key, positive=False):
    value = float(args[key])
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(key + ' must be finite' + (' and positive' if positive else ''))
    return value / 10.0  # Fusion internal length is cm.

def entity(d, token, cls):
    found = d.findEntityByToken(token)
    if not found:
        raise ValueError('Entity no longer resolves; inspect the model again.')
    result = cls.cast(found[0])
    if not result:
        raise ValueError('Wrong entity type.')
    return result

def _execute(op, a):
    if op=='runtime_identity':
        return dict(compatibility.identity(),bridge_path=str(Path(__file__).resolve()),
                    fusion_version=_app.version,queue=str(ROOT))
    if op not in ALLOWED:
        raise ValueError('Unknown operation.')
    if _app.userInterface.activeCommand != 'SelectCommand':
        raise ValueError('Finish the active Fusion command or dialog first.')
    if op == 'new_design':
        if _store is not None:_store.assert_no_uncertain_cloud()
        _app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design().designType = adsk.fusion.DesignTypes.ParametricDesignType
        return inspect()
    if op == 'browse_cloud': return cloud.browse(_app,a)
    if op == 'reconcile_cloud_job':return reporting.response(_store,cloud.reconcile(_store,_app,a['job_id'],a['version_id'],a['confirmation_note']),a.get('section','summary'))
    if op == 'release_edit_token':return cloud.release_token(a['document_id'],a['edit_token'],a['writer_id'])
    d = design()
    if op == 'acquire_edit_token':
        if a['document_id']!=design_id():raise ValueError('Active document changed')
        return reporting.response(_store,cloud.inspect_state(_app,d,design_id(),True,a['writer_id'],a.get('accepted_reference_versions')),a.get('section','summary'))
    if op == 'document_state':
        if a['document_id'] != design_id(): raise ValueError('Active document changed')
        return reporting.response(_store,cloud.inspect_state(_app,d,design_id(),a.get('acquire_token',False)),a.get('section','summary'),a.get('after_revision',''))
    if op == 'inspect':
        return inspect()
    if a.get('design_id') != design_id():
        raise ValueError('TARGET_DOCUMENT_REQUIRED: Active document changed or no design_id supplied. Use inspect_design() and pass its current design_id; an empty or stale ID cannot target the active document.')
    if op == 'inspect_full':
        return model_tools.inspect_full(d, a['include_topology'], a['offset'], a['limit'],a.get('scope'),a.get('include_context',False))
    if op == 'select_geometry':
        body = advanced.native(advanced.resolve(d, a['body_token'], adsk.fusion.BRepBody))
        feature = advanced.resolve(d, a['feature_token']) if a['feature_token'] else None
        matches = model_tools.select(body, a['kind'], a['filters'], feature)
        return {'matches': [model_tools.ref(e) for e in matches], 'count': len(matches),
                'coordinate_system': 'component-local millimetres',
                'selection_is_unique': len(matches) == 1}
    if op == 'measure_distance':
        return model_tools.measure(_app, d, a['one'], a['two'])
    if op == 'check_interference':
        return model_tools.interference(d, a['references'])
    if op == 'validate_model':
        return model_tools.validate(d,a.get('scope'))
    if op == 'audit_hygiene':
        from .hygiene import audit
        return audit(d,a.get('scope'))
    if op in ('rectangle','circle','extrude','parameter','fillet','joint'):
        if cloud._pending: raise ValueError('Cloud save pending; poll before modeling')
        if _store is not None:_store.assert_no_uncertain_cloud()
        cloud.require_edit(_app,d,design_id(),a.get('edit_token',''),
            accepted_reference_versions=a.get('accepted_reference_versions'),writer_id=(a.get('task') or {}).get('writer_id','legacy'))
    if op in advanced.OPS:
        return advanced.execute(op, a, d, _app)
    root = d.rootComponent
    if op in ('rectangle', 'circle'):
        planes = {'XY': root.xYConstructionPlane, 'XZ': root.xZConstructionPlane,
                  'YZ': root.yZConstructionPlane}
        plane = planes[a['plane']]
        x, y = number(a, 'x_mm'), number(a, 'y_mm')
        if op == 'rectangle':
            width, height = number(a, 'width_mm', True), number(a, 'height_mm', True)
        else:
            radius = number(a, 'diameter_mm', True) / 2
        s = root.sketches.add(plane)
        try:
            s.name = a['name']
            p = adsk.core.Point3D.create(x, y, 0)
            if op == 'rectangle':
                s.sketchCurves.sketchLines.addTwoPointRectangle(
                    p, adsk.core.Point3D.create(x + width, y + height, 0))
            else:
                s.sketchCurves.sketchCircles.addByCenterRadius(p, radius)
            return dict(ref(s), profiles=s.profiles.count)
        except Exception:
            s.deleteMe()
            raise
    if op == 'extrude':
        s = entity(d, a['sketch_token'], adsk.fusion.Sketch)
        if s.parentComponent != root:
            raise ValueError('Only root sketches supported.')
        index = a['profile_index']
        if not isinstance(index, int) or not 0 <= index < s.profiles.count:
            raise ValueError('Invalid profile index.')
        if not d.unitsManager.isValidExpression(a['distance'], 'mm'):
            raise ValueError('Invalid length expression.')
        if d.unitsManager.evaluateExpression(a['distance'], 'mm') <= 0:
            raise ValueError('Distance must be positive.')
        operations = {'new_component': adsk.fusion.FeatureOperations.NewComponentFeatureOperation,
                      'new_body': adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                      'join': adsk.fusion.FeatureOperations.JoinFeatureOperation,
                      'cut': adsk.fusion.FeatureOperations.CutFeatureOperation}
        operation = operations[a['operation']]
        target = None
        if a['operation'] == 'cut':
            target = entity(d, a['target_body_token'], adsk.fusion.BRepBody)
            if target.parentComponent != root:
                raise ValueError('Only root bodies supported.')
        features = root.features.extrudeFeatures
        inp = features.createInput(s.profiles.item(index), operation)
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByString(a['distance'])),
            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        if target:
            inp.participantBodies = [target]
        f = features.add(inp)
        f.name = a['name']
        return {'feature': ref(f), 'bodies': [ref(b) for b in items(f.bodies)],
                'health': str(f.healthState), 'message': f.errorOrWarningMessage}
    if op == 'parameter':
        p = d.allParameters.itemByName(a['name'])
        unit = p.unit if p else a['unit']
        if not d.unitsManager.isValidExpression(a['expression'], unit):
            raise ValueError('Invalid parameter expression.')
        if p:
            p.expression = a['expression']
        else:
            p = d.userParameters.add(a['name'], adsk.core.ValueInput.createByString(
                a['expression']), unit, 'Created through Fusion Prompt MCP')
        d.computeAll()
        return inspect()
    if op == 'export':
        filename = a['filename']
        if not filename or any(c in filename for c in '/\\:') or filename in ('.','..'):
            raise ValueError('Provide a filename without directories.')
        fmt = a['format']
        if fmt not in ('step', 'stl') or not filename.lower().endswith('.' + fmt):
            raise ValueError('Filename extension must match format.')
        folder = Path.home() / 'FusionPromptExports'
        folder.mkdir(exist_ok=True)
        path = folder / filename
        if path.exists():
            raise ValueError('Export exists; use a new filename.')
        manager = d.exportManager
        if fmt == 'step':
            options = manager.createSTEPExportOptions(str(path), root)
        else:
            body = entity(d, a['body_token'], adsk.fusion.BRepBody)
            options = manager.createSTLExportOptions(body, str(path))
            options.sendToPrintUtility = False
        if not manager.execute(options):
            raise RuntimeError('Fusion export failed.')
        return {'path': str(path), 'bytes': path.stat().st_size}

def execute(op,a):
    mutating=op in ('rectangle','circle','extrude','parameter','fillet','joint')
    if not mutating or (a.get('task') is None and a.get('scope') is None):return _execute(op,a)
    if not a.get('scope'):raise ValueError('Task-bound narrow operations require explicit scope')
    d=design();selection=scopes.Selection(d,a['scope']);target=d.rootComponent
    owners=[]
    if op=='fillet':
        owners=[advanced.native(advanced.resolve(d,t,adsk.fusion.BRepEdge)).body.parentComponent for t in a['edge_tokens']]
        if not owners:raise ValueError('No edges selected')
        target=owners[0]
    if op=='joint':
        owners=[advanced.resolve(d,a[k],adsk.fusion.Occurrence).component for k in ('occurrence_one','occurrence_two') if a.get(k)]
    if not selection.contains(target,targets=True):raise ValueError('Operation target outside selected targets')
    boundary=scopes.EditBoundary(d,selection,a.get('task'),target)
    for owner in owners:
        if not selection.contains(owner):raise ValueError('Operation owner outside selected scope')
        boundary.require_component(owner)
    if op=='parameter':boundary.require_parameter(a['name'])
    before=scopes.health_snapshot(d)
    budget=None;result={};completed=False;regenerated=False
    try:
        budget=maintainability.Guard(_store,d,selection,a.get('task'),
            getattr(getattr(_app.activeDocument,'dataFile',None),'id',None) or design_id(),uuid.uuid4().hex,'narrow')
        result=_execute(op,a)
        completed=True
        if not d.computeAll():raise RuntimeError('Regeneration failed after narrow operation')
        regenerated=True
    except Exception as exc:
        report=dict(result,execution_status='completed' if completed else 'failed',partial_changes_possible=True,approval_status='not_evaluated',replay_permitted=False)
        if budget:
            try:report['authoring']=budget.finish(completed)
            except Exception as error:report['authoring']={'status':'unproven','message':str(error)}
        try:
            report['edit_boundary']=boundary.post()
            report['validation']=scopes.health_report(d,selection,before)
            report['validation']['validation_status']='unproven'
            report['validation']['inspection_gaps'].append({'check':'failed_operation','message':'Final regeneration not established'})
        except Exception as inspection_error:report['inspection_error']=str(inspection_error)
        report['outcomes']={'execution':report['execution_status'],'regeneration':'completed' if regenerated else 'unproven',
                            'integrity':report.get('validation',{}).get('validation_status','unproven'),'approval':'not_evaluated'}
        detail=reporting.response(_store,report) if _store else report
        raise RuntimeError(str(exc)+'; partial-state report: '+json.dumps(detail)) from exc
    result['execution_status']='completed'
    result['authoring']=budget.finish(True)
    result['edit_boundary']=boundary.post();result['validation']=scopes.health_report(d,selection,before)
    result['approval_status']='not_evaluated'
    result['replay_permitted']=False
    result['outcomes']={'execution':'completed','regeneration':'completed','integrity':result['validation']['validation_status'],
        'edit_boundary':'fail' if result['edit_boundary'].get('violations') else 'pass',
        'authoring':result['authoring']['status'],'evidence':result['validation']['evidence_status'],'approval':'not_evaluated'}
    if result['authoring'].get('blocked') or result['edit_boundary'].get('violations') or result['validation']['feature_errors'] or result['validation']['inspection_gaps'] or result['validation']['evidence_status']!='pass':
        raise RuntimeError('Narrow operation applied with failed postconditions: '+json.dumps(reporting.response(_store,result) if _store else result))
    return result

class Handler(adsk.core.CustomEventHandler):
    def notify(self, args):
        global _busy
        if _busy:
            return
        _busy = True
        try:
            self.process()
        finally:
            _busy = False

    def process(self):
        for request in sorted(ROOT.glob('*.request')):
            work = request.with_suffix('.processing')
            try:
                request.rename(work)
            except FileNotFoundError:
                continue
            try:
                payload = json.loads(work.read_text(encoding='utf-8'))
                if payload['id'] != work.stem:
                    raise ValueError('Request ID mismatch.')
                if time.time() > payload['expires']:
                    raise ValueError('Request expired without execution.')
                if compatibility.mutates(payload['operation'],payload['arguments']):
                    compatibility.require_match(payload.get('caller'))
                result = execute(payload['operation'], payload['arguments'])
                answer = {'ok': True, 'result': result}
            except Exception as exc:
                answer = {'ok': False, 'error': str(exc) +
                          ' Inspect before retrying; some operations may have partially applied.'}
            atomic_json(work.with_suffix('.response'), answer)
            work.unlink(missing_ok=True)
        if _app.userInterface.activeCommand != 'SelectCommand':
            _store.waiting('Finish the active Fusion command/dialog to start the batch.')
            return
        cloud.tick(_store)
        if cloud._pending: return
        job = _store.claim(_owner)
        if job:
            if job['request'].get('kind') == 'cloud':
                cloud.start(_store,job,_app,design,design_id)
            else:
                batch_runner.execute_job(_store, job, _app, design, design_id)

def watch():
    last_beat=0
    while not _stop.wait(0.2):
        if time.monotonic()-last_beat>=1:
            _store.beat(_owner,_busy);last_beat=time.monotonic()
        if any(ROOT.glob('*.request')) or _store.pending():
            _app.fireCustomEvent(EVENT_ID)

def run(context):
    global _app, _event, _handler, _thread, _store, _lock
    _app = adsk.core.Application.get()
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    _store = Store(ROOT)
    _lock = BridgeLock(ROOT)
    _lock.acquire()
    _store.recover()
    cloud.reset()
    # Never replay work left behind by a crash/restart.
    for pattern in ('*.request', '*.processing'):
        for path in ROOT.glob(pattern):
            atomic_json(path.with_suffix('.response'), {
                'ok': False, 'error': 'Bridge restarted. Inspect model before retrying.'})
            path.unlink()
    _stop.clear()
    _event = _app.registerCustomEvent(EVENT_ID)
    _handler = Handler()
    _event.add(_handler)
    _thread = threading.Thread(target=watch, daemon=True)
    _thread.start()

def stop(context):
    _stop.set()
    if _thread:
        _thread.join(timeout=1)
    if _event and _handler:
        _event.remove(_handler)
    if _app:
        _app.unregisterCustomEvent(EVENT_ID)
    _documents.clear()
    cloud.reset()
    if _lock:
        _lock.close()
