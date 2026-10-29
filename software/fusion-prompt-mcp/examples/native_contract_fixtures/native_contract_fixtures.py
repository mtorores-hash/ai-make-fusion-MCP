"""Disposable local fixture. Creates a new document and does not open an existing assembly.

Retains the fixture and temporary receipts beside the run. Cloud first-save, Boolean kernel
diagnostics, and physical checks are outside this script.
"""
import json
from pathlib import Path
import sys
import tempfile
import traceback
import adsk.core
import adsk.fusion
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from FusionPromptBridge import batch_runner,scope,advanced
from FusionPromptBridge.job_store import Store
from native_validation import inspect_runtime, require_runtime


def run(context):
    expected=Path(__file__).resolve().parents[2]
    app=adsk.core.Application.get();out=Path(tempfile.mkdtemp(prefix='fusion-mcp-native-'))
    report={'qualification':'Native fixture only; not production acceptance','cases':[],'source':str(expected)}
    try:
        report['runtime']=inspect_runtime(app,expected)
        require_runtime(report['runtime'])
        document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        document.name='MCP_Disposable_Contract'
        design=adsk.fusion.Design.cast(app.activeProduct);root=design.rootComponent
        def guard():
            if app.activeDocument!=document:raise RuntimeError('Disposable document lost focus')
        store=Store(out/'jobs')
        request=dict(operation_id='native-contract',document_id='disposable-contract',component_token='@root',units='mm',
            script='def run(ctx): return None',checkpoint_before=False,validate_after=False)
        job=store.submit(request);job=store.claim('native-fixture')
        ctx=batch_runner.Context(store,job,app,design,root,guard)
        ctx.parameter('fixture_diameter','10 mm');ctx.parameter('aux_diameter','4 mm')
        base=ctx.parametric_circle('sk_fixture_base','fixture_diameter')
        feature=ctx.native_call('fixture_extrude',lambda:root.features.extrudeFeatures.addSimple(
            base.profiles.item(0),adsk.core.ValueInput.createByString('5 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation),
            target={'component':'@root'})
        feature.name='fixture_extrude';feature.bodies.item(0).name='fixture_body';base.isVisible=False
        spec=scope.selected(design,root);spec['dependency_review']='complete';ctx.selection=scope.Selection(design,spec)
        task=dict(version='1.0',task_id='native-owned-dimension',writer_id='fixture',baseline_id='fixture-baseline',
            allowed_member_ids=['target'],frozen_member_ids=[],allowed_parameter_names=[])
        ctx.boundary=scope.EditBoundary(design,ctx.selection,task,root)
        aux=ctx.parametric_circle('sk_fixture_aux','aux_diameter');aux.isVisible=False;ctx.synchronize()
        boundary=ctx.boundary.post();report['boundary']=boundary
        report['cases'].append({'id':'owned_generated_dimension','pass':not boundary['violations'] and bool(boundary['owned_generated_parameters'])})
        before=ctx._synchronized_revision_state()
        try:
            report['export']=ctx.export_checked('fixture.step',scope=ctx.selection.current_spec(),
                manual_review_note='Disposable native fixture; root body and unused auxiliary profile intentionally retained.')
            report['cases'].append({'id':'checked_export_solved_state','pass':ctx._synchronized_revision_state()==before})
        except Exception as exc:
            report['cases'].append({'id':'checked_export_solved_state','pass':False,'error':str(exc)})
        def camera_state():
            camera=app.activeViewport.camera
            return {name:list(getattr(camera,name).asArray()) for name in ('eye','target','upVector')}
        camera_before=camera_state()
        report['presentation']=ctx.present(eye=(30,30,30),target=(0,0,0),width=1920,height=1080)
        report['camera_before']=camera_before;report['camera_after']=camera_state()
        report['cases'].append({'id':'presentation_no_observed_model_change','pass':report['presentation']['status']=='pass'})
        report['cases'].append({'id':'camera_restored','pass':all(
            abs(a-b)<=1e-9 for name in camera_before for a,b in zip(camera_before[name],report['camera_after'][name]))})
        report['activity']=store.events(ctx.job_id)
        report['all_passed']=all(r['pass'] for r in report['cases'])
        store.finish(ctx.job_id,'succeeded' if report['all_passed'] else 'failed',ctx.result)
    except Exception:
        report['traceback']=traceback.format_exc();report['all_passed']=False
    finally:
        (out/'native-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        app.userInterface.messageBox('Disposable fixture retained. Review actual results: '+str(out/'native-result.json'))
