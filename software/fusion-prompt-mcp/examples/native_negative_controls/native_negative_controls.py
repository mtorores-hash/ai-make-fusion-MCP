"""Disposable real-model controls. Restart/capture failures are explicitly injected, not real crashes."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import traceback
from types import SimpleNamespace
import adsk.core
import adsk.fusion
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from FusionPromptBridge import batch_runner,cloud,scope,maintainability,authoring_recovery,compatibility
from FusionPromptBridge.job_store import Store,BridgeLock
from native_validation import inspect_runtime,require_runtime


def run(context):
    app=adsk.core.Application.get();out=Path(tempfile.mkdtemp(prefix='fusion-080-negative-'))
    report={'qualification':'Native disposable model; injected restart journal and capture failure, not real process crash/viewport diagnosis','cases':[]}
    lock=None
    def case(name,passed,**detail):
        report['cases'].append(dict(id=name,passed=bool(passed),**detail))
        if not passed:raise RuntimeError('Control failed: '+name)
    try:
        report['runtime']=inspect_runtime(app,Path(__file__).resolve().parents[2]);require_runtime(report['runtime'])
        document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);document.name='MCP_080_Disposable_Negative_Controls';document_id='negative-fixture'
        design=adsk.fusion.Design.cast(app.activeProduct);root=design.rootComponent
        def guard():
            if app.activeDocument!=document:raise RuntimeError('Disposable fixture lost focus')
        store=Store(out/'jobs');lock=BridgeLock(store.root);lock.acquire()
        def request(operation):return dict(operation_id=operation,document_id=document_id,component_token='@root',units='mm',script='def run(ctx): return None',checkpoint_before=False,validate_after=False)
        job=store.submit(request('seed'));job=store.claim('fixture');ctx=batch_runner.Context(store,job,app,design,root,guard)
        ctx.parameter('fixture_diameter','10 mm');height=ctx.parameter('fixture_height','5 mm');foreign=ctx.parameter('foreign_control','1 mm')
        sketch=ctx.parametric_circle('sk_source','fixture_diameter')
        feature=root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),ctx.value('fixture_height'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        feature.name='Fixture_Source_Extrude';sketch.isVisible=False;ctx.synchronize()
        cloud.inspect_state(app,design,document_id,False)
        token=cloud.inspect_state(app,design,document_id,writer_id='fixture')['edit_token']
        foreign.expression='2 mm'
        try:cloud.require_edit(app,design,document_id,token,writer_id='fixture');rejected=False
        except ValueError as exc:rejected='changed since inspection' in str(exc)
        case('stale_token_rejects_actual_parameter_edit',rejected)
        cloud.release_token(document_id,token,'fixture');foreign.expression='1 mm';ctx.synchronize()
        frozen=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component;frozen.name='Frozen_Control'
        def spec():
            chosen=scope.selected(design,root);chosen['dependency_review']='complete'
            chosen['members'].append(dict(id='frozen',component_token=frozen.entityToken,revision=frozen.revisionId,membership='active',maturity='frozen',role='authored'))
            return chosen
        task=dict(version='1.0',task_id='negative',writer_id='fixture',baseline_id='disposable',allowed_member_ids=['target'],frozen_member_ids=['frozen'],allowed_parameter_names=['fixture_height'])
        boundary=scope.EditBoundary(design,scope.Selection(design,spec()),task,root)
        foreign.expression='2 mm';violations=boundary.post()['violations']
        case('foreign_parameter_change_detected',any(v.get('name')=='foreign_control' for v in violations),violations=violations)
        foreign.expression='1 mm';ctx.synchronize()
        boundary=scope.EditBoundary(design,scope.Selection(design,spec()),task,root)
        ctx.target=frozen
        try:ctx.parametric_circle('sk_intentionally_forbidden','fixture_diameter')
        finally:ctx.target=root
        case('frozen_component_edit_detected',bool(boundary.post()['violations']))
        # Retain deliberate negative geometry. New baseline starts after those controls.
        store.finish(ctx.job_id,'succeeded',ctx.result)
        original=store.submit(request('injected-interrupted-budget'));original=store.claim('fixture')
        original_ctx=batch_runner.Context(store,original,app,design,root,guard)
        original_ctx.selection=scope.Selection(design,spec())
        policy=dict(max_new_features=0,max_new_sketches=0,cumulative_new_features=0,cumulative_new_sketches=0,max_attempts=3,max_seconds=60,
                    source_feature_tokens=[feature.entityToken],planned_operations=['edit source height'],protected_member_ids=['frozen'],strategy_revision='A',strategy_note='Source dimension edit',budget_reason='No new history required')
        budget_task=dict(task,issue_id='disposable-native-ledger',authoring=policy)
        maintainability.Guard(store,design,original_ctx.selection,budget_task,document_id,original['operation_id'])
        height.expression='6 mm';original_ctx.synchronize()
        store.recover()  # Explicit injected journal restart on this isolated local queue only.
        original_ctx.request=dict(original_ctx.request,mode='reconcile');original_ctx.selection=scope.Selection(design,spec())
        proposal=authoring_recovery.inspect(original_ctx,budget_task['issue_id'],original['job_id'])
        case('protected_revision_ambiguity_stays_blocked',any(b.startswith('protected_component_changed:') for b in proposal['blockers']),proposal=proposal)
        # Native revisions can propagate into a protected child. Retain that blocked
        # ledger; use a separate root-only document to qualify positive accounting.
        document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);document.name='MCP_080_Disposable_Ledger_Continuation';document_id='root-only-fixture'
        design=adsk.fusion.Design.cast(app.activeProduct);root=design.rootComponent
        seed=store.submit(request('positive-seed'));seed=store.claim('fixture')
        ctx=batch_runner.Context(store,seed,app,design,root,guard)
        ctx.parameter('fixture_diameter','10 mm');height=ctx.parameter('fixture_height','5 mm')
        sketch=ctx.parametric_circle('sk_source','fixture_diameter')
        feature=root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),ctx.value('fixture_height'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        feature.name='Fixture_Source_Extrude';sketch.isVisible=False;ctx.synchronize()
        store.finish(ctx.job_id,'succeeded',ctx.result)
        def spec():
            chosen=scope.selected(design,root);chosen['dependency_review']='complete';return chosen
        task=dict(task,frozen_member_ids=[])
        policy=dict(policy,source_feature_tokens=[feature.entityToken],protected_member_ids=[])
        budget_task=dict(task,issue_id='disposable-root-only-ledger',authoring=policy)
        original=store.submit(request('injected-root-only-interruption'));original=store.claim('fixture')
        original_ctx=batch_runner.Context(store,original,app,design,root,guard)
        original_ctx.selection=scope.Selection(design,spec())
        maintainability.Guard(store,design,original_ctx.selection,budget_task,document_id,original['operation_id'])
        height.expression='6 mm';original_ctx.synchronize();store.recover()
        original_ctx.request=dict(original_ctx.request,mode='reconcile')
        original_ctx.selection=scope.Selection(design,spec())
        proposal=authoring_recovery.inspect(original_ctx,budget_task['issue_id'],original['job_id'])
        case('interrupted_native_attempt_observable',not proposal['blockers'],proposal=proposal)
        height.expression='7 mm';original_ctx.synchronize()
        try:authoring_recovery.acknowledge(original_ctx,budget_task['issue_id'],proposal['observation_id'],'Deliberately stale',original['job_id']);rejected=False
        except ValueError as exc:rejected='Stale' in str(exc)
        case('stale_ledger_observation_rejected',rejected)
        original_ctx.selection=scope.Selection(design,spec())
        proposal=authoring_recovery.inspect(original_ctx,budget_task['issue_id'],original['job_id'])
        token=cloud.inspect_state(app,design,document_id,writer_id='fixture')['edit_token']
        cloud.require_edit(app,design,document_id,token,writer_id='fixture')
        receipt=authoring_recovery.acknowledge(original_ctx,budget_task['issue_id'],proposal['observation_id'],'Observed retained height edit; preserve source and charge interrupted budget',original['job_id'])
        case('ledger_ack_preserves_original_and_budget',receipt['attempts']==1 and not receipt['replayed'] and store.result(original['job_id'])['status']=='interrupted',receipt=receipt)
        try:maintainability.Guard(store,design,original_ctx.selection,budget_task,document_id,'same-strategy');rejected=False
        except ValueError as exc:rejected='changed strategy' in str(exc)
        case('unchanged_strategy_stays_blocked',rejected)
        revised=copy.deepcopy(budget_task);revised['authoring']['strategy_revision']='B';revised['authoring']['strategy_note']='Inspect retained edit; no growth corrective hypothesis'
        resumed=maintainability.Guard(store,design,original_ctx.selection,revised,document_id,'new-hypothesis')
        result=resumed.finish(True);case('remaining_budget_continuation',resumed.status['attempt']==2 and result['cumulative_growth']=={'features':0,'sketches':0},authoring=result)
        # Real native model with an injected I/O failure, distinct from native viewport diagnosis.
        capture_job=store.submit(dict(request('capture-injection'),mode='read_only'));capture_job=store.claim('fixture')
        capture_ctx=batch_runner.Context(store,capture_job,app,design,root,guard)
        before=capture_ctx._synchronized_revision_state();capture_ctx.record('retained_measurement_mm',7)
        capture_ctx.app=SimpleNamespace(activeViewport=SimpleNamespace(saveAsImageFile=lambda *args:False))
        try:failure=capture_ctx.capture('injected_failure.png',required=False)
        finally:capture_ctx.app=app
        store.finish(capture_ctx.job_id,'succeeded',capture_ctx.result)
        case('optional_capture_failure_preserves_native_state',failure['status']=='failed' and before==capture_ctx._synchronized_revision_state() and store.result(capture_ctx.job_id)['result']['measurements']['retained_measurement_mm']==7,failure=failure)
        report['all_passed']=all(c['passed'] for c in report['cases'])
    except Exception:report['all_passed']=False;report['error']=traceback.format_exc()
    finally:
        if lock:lock.close()
        (out/'native-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        app.userInterface.messageBox('Disposable negative controls retained: '+str(out/'native-result.json'))

