"""Synthetic K1 failure controls. API doubles, never native/kernel qualification."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import zlib
import test_batch_runner as batch_fixture
import test_scoped_workflow as scope_fixture
import test_cloud as cloud_fixture
from test_advanced import Node, Collection
from FusionPromptBridge import reporting, scope, preservation, maintainability, png_check, cloud
from FusionPromptBridge.job_store import Store, canonical


class K1Tests(unittest.TestCase):
    def fixture(self,cls):
        case=cls();case.setUp();self.addCleanup(case.doCleanups);return case
    def store(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);return Store(tmp.name)

    def test_compact_inventory_paging_delta_and_stale_guard(self):
        f=self.fixture(cloud_fixture.CloudTests);s=self.store()
        f.design.allParameters=Collection([Node(name='p'+str(i),expression='1 mm') for i in range(10000)])
        full=cloud.inspect_state(f.app,f.design,'doc',False);r=reporting.response(s,full)
        self.assertLess(len(canonical(r)),1800);self.assertEqual(r['counts']['parameters'],10000)
        self.assertTrue(reporting.response(s,full,after_revision=r['revision'])['unchanged'])
        pieces=[];offset=0
        while True:
            page=reporting.page(s,r['detail']['report_id'],'raw',offset,4096);pieces.append(page['text'])
            if page['next_offset'] is None:break
            offset=page['next_offset']
        reconstructed=''.join(pieces).encode()
        self.assertEqual(hashlib.sha256(reconstructed).hexdigest(),r['detail']['sha256'])
        token=reporting.response(s,cloud.inspect_state(f.app,f.design,'doc'))['edit_token']
        f.design.allParameters.item(500).expression='2 mm'
        with self.assertRaisesRegex(ValueError,'changed since inspection'):f.guard(token)
        later=reporting.response(s,cloud.inspect_state(f.app,f.design,'doc',False))
        delta=reporting.page(s,later['revision'],'delta',baseline_report_id=r['revision'])
        self.assertEqual(delta['items'],[dict(name='p500',before='1 mm',after='2 mm')])
        self.assertEqual(json.loads(reconstructed)['parameters'][500][1],'1 mm')

    def test_compact_blockers_and_large_entry_are_not_silent_passes(self):
        s=self.store();full={'result':{'validation':{'inspection_gaps':[{'message':'unavailable'}]*40},'files':[{'path':'x','huge':'x'*10000}]}}
        r=reporting.response(s,full)
        self.assertEqual((r['blocker_count'],r['blockers_omitted']),(40,32))
        self.assertTrue(r['details_omitted'])
        page=reporting.page(s,r['revision'],'/result/files');self.assertTrue(page['items'][0]['detail_omitted'])
        self.assertEqual(r['telemetry']['response_bytes'],len(canonical(r).encode()))

    def test_unavailable_health_does_not_hide_other_damage(self):
        f=self.fixture(scope_fixture.WorkflowTests)
        broken=f.feature('broken-joint');broken.occurrenceOne=None;broken.occurrenceTwo=None
        f.part.asBuiltJoints=Collection([Node(entityToken='unsupported',occurrenceOne=None,occurrenceTwo=None),broken])
        r=scope.health_report(f.design,f.selection())
        self.assertEqual(len(r['inspection_gaps']),1);self.assertEqual(len(r['feature_errors']),1)
        self.assertEqual(r['validation_status'],'fail')

    def test_completed_work_survives_unavailable_health_and_missing_optional_capture(self):
        f=self.fixture(batch_fixture.BatchTests)
        f.target.asBuiltJoints=Collection([Node(entityToken='joint-no-health',occurrenceOne=None,occurrenceTwo=None)])
        f.app.activeViewport=Node(saveAsImageFile=Mock(return_value=True))
        request=dict(f.req,script='def run(ctx):\n    ctx.record("fit_mm",2)\n    p=ctx.path("fixture.step")\n    p.write_text("synthetic receipt, not CAD")\n    ctx.artifact(p)\n    ctx.capture(required=False)\n    return {"completed":True}')
        r=f.run_job(request)['result']
        self.assertEqual(r['return_value'],{'completed':True});self.assertEqual(r['measurements']['fit_mm'],2)
        self.assertEqual(len(r['files']),1);self.assertEqual(r['outcomes']['integrity'],'unproven')
        self.assertEqual(r['outcomes']['execution'],'completed');self.assertEqual(r['outcomes']['presentation'],'failed')
        self.assertFalse(r['replay_permitted'])
        persisted=f.store.result(f.store.list()[0]['job_id'])['result'];self.assertEqual(persisted['files'],r['files'])

    def test_native_operation_visible_while_blocked_cancel_pending_restart_no_replay(self):
        f=self.fixture(batch_fixture.BatchTests);ctx=f.context();entered=threading.Event();release=threading.Event();errors=[]
        def action():entered.set();release.wait(3)
        def run():
            try:ctx.native_call('combine_cut',action,target={'token':'fixture-target'},tools=['cutter'])
            except Exception as exc:errors.append(exc)
        worker=threading.Thread(target=run);worker.start()
        try:
            self.assertTrue(entered.wait(2));f.store.beat('worker',True)
            status=f.store.cancel(ctx.job_id)
            self.assertEqual(status['activity']['kind'],'operation_started')
            self.assertEqual(status['activity']['data']['operation'],'combine_cut')
            self.assertEqual(status['cancellation'],'pending_cooperative_boundary')
            self.assertTrue(status['bridge_liveness']['observed_fresh'])
            f.store.recover();self.assertIsNone(f.store.claim('restart'))
            self.assertEqual(f.store.result(ctx.job_id)['result']['outcomes']['mutation'],'uncertain_after_restart')
        finally:release.set();worker.join(3)
        self.assertFalse(errors)
        events=f.store.events(ctx.job_id);self.assertEqual(events['events'][0]['data']['tools'],['cutter'])
        self.assertTrue(f.store.events(ctx.job_id,events['cursor'])['unchanged'])

    def test_generated_dimension_ownership_and_foreign_changes(self):
        f=self.fixture(scope_fixture.WorkflowTests);boundary=scope.EditBoundary(f.design,f.selection(),f.task(),f.part)
        dimension=Node(createdBy=Node(),component=f.part,name='d101',expression='2 mm')
        f.design.allParameters.values.append(dimension)
        self.assertFalse(boundary.post()['violations'])
        dimension.component=f.other
        self.assertEqual(boundary.post()['violations'][0]['kind'],'parameter')
        dimension.component=f.part
        before=scope.EditBoundary(f.design,f.selection(),f.task(),f.part)
        dimension.expression='3 mm'
        self.assertEqual(before.post()['violations'][0]['kind'],'parameter') # Existing dimensions still require permission.

    def test_protected_guid_roundoff_and_small_real_change(self):
        f=self.fixture(scope_fixture.WorkflowTests)
        f.spec['members'].append(f.member('supplier',f.supplier,'purchased','frozen'))
        body=f.supplier.bRepBodies.item(0)
        boundary=scope.EditBoundary(f.design,f.selection(),f.task(),f.part)
        f.supplier.revisionId='propagated';body.volume+=1.82e-15 # cm3 => 1.82e-12 mm3
        r=boundary.post();self.assertFalse(r['violations']);self.assertEqual(r['revision_attribution'][0]['classification'],'revision_propagation')
        body.revisionId='real-edit'
        self.assertTrue(boundary.post()['violations']) # Even equal volume/bounds cannot hide body revision.
        body.revisionId='br1';body.volume+=1e-5
        self.assertTrue(boundary.post()['violations'])
        body.volume=1;f.supplier.sketches.values.append(Node())
        self.assertTrue(boundary.post()['violations'])

    def policy(self):
        return dict(max_new_features=1,max_new_sketches=0,cumulative_new_features=3,cumulative_new_sketches=0,
            max_attempts=3,max_seconds=60,source_feature_tokens=['source'],planned_operations=['source_parameter_edit'],
            strategy_revision='A',strategy_note='Edit controlling feature',budget_reason='One purposeful feature maximum',protected_member_ids=[])
    def budget_fixture(self):
        f=self.fixture(scope_fixture.WorkflowTests);source=f.feature('source',0);source.parentComponent=f.part
        f.part.features.values.append(source);f.refs['source']=source;s=self.store();task=dict(f.task(),authoring=self.policy())
        return f,s,task

    def test_issue_budget_survives_jobs_agent_names_and_history_flattening(self):
        f,s,task=self.budget_fixture()
        first=maintainability.Guard(s,f.design,f.selection(),task,'doc','job1')
        f.part.features.values.extend([f.feature('patch1',0),f.feature('patch2',0)])
        self.assertEqual(first.finish(True)['status'],'fail')
        with self.assertRaisesRegex(ValueError,'changed strategy'):
            maintainability.Guard(s,f.design,f.selection(),dict(task,writer_id='another-agent'),'doc','job2')
        with self.assertRaisesRegex(ValueError,'unresolved authoring issue'):
            maintainability.Guard(s,f.design,f.selection(),dict(task,issue_id='rename'),'doc','job3')
        omitted=dict(task);omitted.pop('authoring')
        with self.assertRaisesRegex(ValueError,'unresolved authoring issue'):maintainability.Guard(s,f.design,f.selection(),omitted,'doc','job4')
        corrected=copy.deepcopy(task);corrected['authoring']['strategy_revision']='B'
        next_attempt=maintainability.Guard(s,f.design,f.selection(),corrected,'doc','job5')
        f.part.features.values[:]=[f.feature('flattened',0)]
        r=next_attempt.finish(True)
        self.assertIn('history_removed_requires_separate_isolated_rebuild_review',r['violations'])
        self.assertEqual(r['cumulative_growth']['features'],3)

    def test_legitimate_parameter_edit_and_changed_token_text_do_not_count_as_growth(self):
        f,s,task=self.budget_fixture()
        guard=maintainability.Guard(s,f.design,f.selection(),task,'doc','job1')
        f.part.features.item(0).entityToken='same-object-new-token'
        self.assertEqual(guard.finish(True)['growth'],{'features':0,'sketches':0})
        self.assertEqual(guard.status['status'],'pass')

    def test_interrupted_budget_blocks_new_operation_without_reset(self):
        f,s,task=self.budget_fixture();maintainability.Guard(s,f.design,f.selection(),task,'doc','job1')
        with self.assertRaisesRegex(ValueError,'uncertain effects'):
            maintainability.Guard(s,f.design,f.selection(),task,'doc','job2')

    def test_budget_enforced_through_batch_and_narrow_dispatch(self):
        f,s,task=self.budget_fixture()
        f.app.activeDocument.dataFile=None
        token=cloud.inspect_state(f.app,f.design,'doc',writer_id='writer')['edit_token']
        req=dict(operation_id='batch-growth',document_id='doc',component_token='carrier',units='mm',edit_token=token,
            script='def run(ctx):\n    import types\n    target.features.values.extend([types.SimpleNamespace(entityToken="a",isValid=True,healthState=0,errorOrWarningMessage=""),types.SimpleNamespace(entityToken="b",isValid=True,healthState=0,errorOrWarningMessage="")])\n    return "modeled"',
            checkpoint_before=False,validate_after=True,scope=f.spec,task=task)
        job=s.submit(req)
        batch_fixture.runner.execute_job(s,s.claim('owner'),f.app,lambda:f.design,lambda:'doc')
        r=s.result(job['job_id']);self.assertEqual(r['result']['return_value'],'modeled')
        self.assertEqual(r['status'],'failed');self.assertEqual(r['result']['outcomes']['authoring'],'fail')
        # A separate disposable component/task exercises the narrow dispatcher.
        f,s,task=self.budget_fixture();source=f.part.features.item(0)
        f.root.features.values=[source];source.parentComponent=f.root
        f.spec=scope.selected(f.design,f.root);f.spec['dependency_review']='complete'
        task['allowed_member_ids']=['target'];task['issue_id']='narrow-issue'
        def mutate(op,args):
            f.root.features.values.extend([f.feature('a',0),f.feature('b',0)]);return {'created_token':'a'}
        dispatch=f.dispatcher(mutate);dispatch.__globals__['_store']=s
        with self.assertRaisesRegex(RuntimeError,'failed postconditions') as caught:
            dispatch('rectangle',{'scope':f.spec,'task':task})
        self.assertIn('features_growth',str(caught.exception));self.assertEqual(f.root.features.count,3)

    def test_readonly_presentation_failure_preserves_model_and_does_not_solve(self):
        f=self.fixture(batch_fixture.BatchTests)
        f.app.activeViewport=Node(camera=Node(),saveAsImageFile=Mock(return_value=True))
        f.design.computeAll=Mock(side_effect=AssertionError('Presentation regenerated'))
        r=f.run_job(dict(f.req,mode='read_only',script='def run(ctx): return ctx.present()'))['result']
        self.assertEqual(r['return_value']['capture']['status'],'failed')
        self.assertFalse(r['return_value']['observation']['model_changed']);f.design.computeAll.assert_not_called()

    def test_export_sync_reuses_exact_solved_state_but_not_parameter_edits(self):
        f=self.fixture(batch_fixture.BatchTests);ctx=f.context();f.design.computeAll=Mock(return_value=True)
        f.target.bRepBodies=Collection([Node()]);f.target.occurrences=Collection()
        ctx.synchronize();self.assertEqual(f.design.computeAll.call_count,1)
        # A complete scope is supplied, independent from the legacy migration default.
        spec=scope.selected(f.design,f.target);spec['dependency_review']='complete'
        with patch.object(ctx,'require_hygiene',return_value={}),patch.object(ctx,'export',return_value={'path':'part.step'}):
            ctx.export_checked('part.step',manual_review_note='Synthetic control',scope=spec)
            self.assertEqual(f.design.computeAll.call_count,1)
            f.design.allParameters.values.append(Node(name='x',expression='2 mm'))
            ctx.export_checked('other.step',manual_review_note='Synthetic control',scope=spec)
            self.assertEqual(f.design.computeAll.call_count,2)
            def propagate():f.target.revisionId='r2';return True
            f.design.allParameters.item(0).expression='3 mm';f.design.computeAll.side_effect=propagate
            with self.assertRaisesRegex(ValueError,'revision'):ctx.export_checked('stale.step',manual_review_note='x',scope=spec)

    def test_first_save_waits_for_remote_metadata_without_replaying(self):
        f=self.fixture(cloud_fixture.CloudTests);f.doc.isSaved=False;f.doc.dataFile=None;f.doc.saveAs=Mock(return_value=True)
        with patch.object(cloud,'destination',return_value=Node(id='folder')):
            ident=f.run_job('save',dict(document_id='doc',edit_token=f.token(),name='housing'))
        f.doc.dataFile=f.file;f.app.data.findFileById=Mock(return_value=None)
        cloud.tick(f.store);self.assertEqual(f.store.status(ident)['status'],'running')
        f.app.data.findFileById.return_value=f.file;cloud.tick(f.store)
        self.assertEqual(f.store.status(ident)['status'],'succeeded');f.doc.saveAs.assert_called_once()
        cloud.tick(f.store);f.doc.saveAs.assert_called_once()

    def test_first_save_wrong_destination_stays_uncertain(self):
        f=self.fixture(cloud_fixture.CloudTests);f.doc.isSaved=False;f.doc.dataFile=None;f.doc.saveAs=Mock(return_value=True)
        with patch.object(cloud,'destination',return_value=Node(id='wanted')):
            ident=f.run_job('save',dict(document_id='doc',edit_token=f.token(),name='housing'))
        f.doc.dataFile=f.file;cloud.tick(f.store)
        self.assertEqual(f.store.status(ident)['status'],'failed')
        with self.assertRaisesRegex(ValueError,'destination'):cloud.reconcile(f.store,f.app,ident,'version-1','Observed')
        with self.assertRaisesRegex(ValueError,'Uncertain cloud'):f.store.assert_no_uncertain_cloud()
        f.doc.saveAs.assert_called_once()

    def test_png_decoder_rejects_header_only_and_corrupt_raster(self):
        s=self.store();p=s.root/'view.png'
        def chunk(kind,value):return struct.pack('>I',len(value))+kind+value+struct.pack('>I',zlib.crc32(kind+value)&0xffffffff)
        header=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2,1,8,2,0,0,0))
        p.write_bytes(header)
        with self.assertRaisesRegex(ValueError,'Incomplete'):png_check.dimensions(p)
        p.write_bytes(header+chunk(b'IDAT',zlib.compress(b'\x00'+b'\x01'*6))+chunk(b'IEND',b''))
        self.assertEqual(png_check.dimensions(p),(2,1))
        p.write_bytes(header+chunk(b'IDAT',zlib.compress(b'\x00'+b'\x01'*3))+chunk(b'IEND',b''))
        with self.assertRaisesRegex(ValueError,'raster'):png_check.dimensions(p)


if __name__=='__main__':unittest.main()
