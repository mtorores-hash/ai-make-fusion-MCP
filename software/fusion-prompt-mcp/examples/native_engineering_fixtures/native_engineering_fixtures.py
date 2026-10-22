"""Manual Fusion Scripts and Add-Ins runner. Creates ONLY a new disposable document.

Not executed/qualified in the development container. No cloud save, installs or live
assembly access. Leave created fixture open for visual review. Results/checkpoints
go to a new system temporary directory, whose path is shown on completion/error.
"""
import json
import sys
import tempfile
import time
import traceback
from pathlib import Path
import adsk.core
import adsk.fusion

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from FusionPromptBridge import batch_runner, design_intent, engineering, model_tools, recovery, scope
from FusionPromptBridge.job_store import Store
from native_validation import inspect_runtime, require_runtime


def make_box(root,name,lo,hi):
    sketch=root.sketches.add(root.xYConstructionPlane);sketch.name='fixture_'+name
    if lo[2]!=0:raise ValueError('Fixture builder currently requires z=0')
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(lo[0]/10,lo[1]/10,0),
                                                       adsk.core.Point3D.create(hi[0]/10,hi[1]/10,0))
    if sketch.profiles.count!=1:raise RuntimeError('Fixture rectangle did not produce one profile')
    feature=root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),
        adsk.core.ValueInput.createByString(str(hi[2])+' mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    if feature.bodies.count!=1:raise RuntimeError('Fixture did not produce one solid')
    body=feature.bodies.item(0);body.name=name;sketch.isVisible=False
    return body,feature


def only_face(body,x_mm):
    matches=model_tools.select(body,'face',{'geometry_type':'Plane','normal_parallel_to':[1,0,0],
                                          'at_coordinate_mm':{'x':x_mm},'tolerance_mm':.001})
    if len(matches)!=1:raise RuntimeError('Fixture face selector ambiguous/missing')
    return matches[0]


def run(context):
    app=adsk.core.Application.get();out=Path(tempfile.mkdtemp(prefix='fusion-mcp-engineering-'))
    result={'qualification':'native run; explicit finite fixtures only','output_directory':str(out),'cases':[]}
    try:
        result['runtime']=inspect_runtime(app,Path(__file__).resolve().parents[2])
        require_runtime(result['runtime'])
        document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        document.name='MCP_Disposable_Engineering_Fixtures'
        design=adsk.fusion.Design.cast(app.activeProduct);root=design.rootComponent
        def guard():
            if app.activeDocument!=document:raise RuntimeError('Fixture document lost focus; stopped')
        store=Store(out/'jobs');counter=[0]
        def ctx(label):
            guard();counter[0]+=1
            request=dict(operation_id='native-'+str(counter[0]),document_id='isolated-native-fixture',component_token=root.entityToken,
                units='mm',script='def run(ctx):\n    return {}',checkpoint_before=False,validate_after=False)
            job=store.submit(request);store.claim('native-fixture');job['request']=request
            current=batch_runner.Context(store,job,app,design,root,guard)
            spec=scope.selected(design,root);spec['dependency_review']='complete'
            current.selection=scope.Selection(design,spec);return current
        def finish(current):store.finish(current.job_id,'succeeded',current.result)
        a,origin=make_box(root,'continuous_wall_lower',[0,0,0],[4,10,10])
        b,_=make_box(root,'stepped_wall_upper',[.3,10,0],[4.3,20,10])
        screw,_=make_box(root,'screw_head',[30,0,0],[34,4,3])
        cover,_=make_box(root,'screwdriver_obstruction',[29,-1,0],[35,5,15])
        pcb,_=make_box(root,'pcb_volume',[50,0,0],[70,20,1.6])
        lid,_=make_box(root,'wire_obstruction',[69,0,0],[74,20,12])
        fa=only_face(a,0);fb=only_face(b,.3)
        def reference(e,**fields):return dict(reference=model_tools.ref(e),**fields)
        def envelope(body,lo,hi):return {'frame':'world_mm','min_mm':lo,'max_mm':hi,
            'source':'explicit disposable fixture envelope','geometry_revision':body.revisionId}
        plan={'version':'1.0','document_id':'isolated-native-fixture','interfaces':{
            'lower':reference(fa,protected=True),'upper':reference(fb),
            'screw':reference(screw,envelopes={'driver':envelope(screw,[30,0,3],[34,4,25])}),
            'cover':reference(cover),'pcb':reference(pcb,envelopes={'connected_wire':envelope(pcb,[67,5,1.6],[78,15,10])}),
            'lid':reference(lid)},'checks':[
                {'id':'wall_step','kind':'continuous_wall','interfaces':['lower','upper'],
                 'limits':{'step_mm':.05,'gap_mm':.05,'normal_angle_deg':.1}}]}
        for name,moving,envelope_name,obstacle,operation in [('screw_access','screw','driver','cover','screwdriver'),
                        ('wire_clearance','pcb','connected_wire','lid','connected_wire')]:
            plan['checks'].append({'id':name,'kind':'access','operation':operation,'moving':moving,'envelope':envelope_name,
                'obstacles':[obstacle],'translations_mm':[[0,0,0]],'max_samples':1,'limits':{'max_volume_mm3':0}})
        current=ctx('defects');start=time.perf_counter();report=engineering.verify(current,plan)
        result['verification']={'seconds':time.perf_counter()-start,'summary_bytes':len(json.dumps(report).encode()),'context_calls':1,'summary':report}
        for name in ('wall_step','screw_access','wire_clearance'):
            result['cases'].append({'id':name,'expected':'fail','actual':next(c['status'] for c in report['checks'] if c['id']==name)})
        finish(current)
        # Explicit seam control: the same 0.3 mm separation is intentional.
        seam=dict(plan,checks=[{'id':'intentional_seam','kind':'gap','interfaces':['lower','upper'],
                               'limits':{'min_mm':.25,'max_mm':.35},'intent_reason':'declared part seam'}])
        current=ctx('seam');r=engineering.verify(current,seam);finish(current)
        result['cases'].append({'id':'intentional_seam','expected':'pass','actual':r['checks'][0]['status']})
        # Fault injection makes the feature token stale; an actual bounded native edit
        # changes the opposite solid while the tagged mounting datum is protected.
        design_intent.tag_geometry(design,a,'fixture_mount','face',{'at_coordinate_mm':{'x':0}},origin,
                                   signature_tolerances={},allow_feature_fallback=True)
        reader=ctx('baseline');baseline=engineering.Session(reader,plan).protected();finish(reader)
        make_box(root,'bounded_added_rib',[100,0,0],[101,5,5]);design.computeAll()
        attribute=a.attributes.itemByName(design_intent.GROUP,'fixture_mount');definition=json.loads(attribute.value)
        definition['feature_token']='deliberately-invalid-fixture-token';attribute.value=json.dumps(definition)
        recovered=design_intent.resolve_tag(design,'fixture_mount',True)
        reader=ctx('protected')
        result['reference_recovery']={'fault_injection':True,'result':recovered,
            'protected':engineering.compare_protected(baseline,engineering.Session(reader,plan).protected())}
        finish(reader)
        # Persist one completed mutation, then fail immediately after a second mutation.
        current=ctx('interrupt');current.result['before_observation']=recovery.observe(current);calls=[]
        def action_one(c):calls.append('one');return model_tools.ref(make_box(root,'stage_one',[110,0,0],[112,2,2])[0])
        def action_two(c):
            calls.append('two');make_box(root,'stage_two',[120,0,0],[122,2,2]);raise RuntimeError('Injected interruption after mutation')
        recovery.run_stage(current,'one',action_one,lambda c:{'status':'pass' if root.bRepBodies.itemByName('stage_one') else 'fail'},plan)
        try:recovery.run_stage(current,'two',action_two,lambda c:{'status':'unproven'},plan)
        except RuntimeError:pass
        store.finish(current.job_id,'interrupted',current.result)
        reader=ctx('reconcile');result['recovery']=recovery.reconcile(reader,current.job_id);finish(reader)
        result['recovery']['action_invocations']=calls
        result['all_declared_defect_cases_matched']=all(c['actual']==c['expected'] for c in result['cases'])
        result['not_checked']=['real_process_crash','STDIO_transport','nested_occurrence_transforms','G1_G2_native_evaluators','manufacturing_exports','slicer','physical_assembly']
    except Exception:
        result['all_declared_defect_cases_matched']=False
        result['error']=traceback.format_exc()
    finally:
        (out/'native-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        app.userInterface.messageBox('Disposable fixture run finished. Review errors/statuses; no cloud save.\n'+str(out/'native-result.json'))
