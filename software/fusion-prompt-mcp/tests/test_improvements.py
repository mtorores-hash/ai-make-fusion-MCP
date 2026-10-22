"""Compatibility and reconciliation regression controls: API doubles, not kernel claims."""
import ast
import copy
import json
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import test_k1_regressions as k1_fixture
from FusionPromptBridge import authoring_recovery as recovery,maintainability,compatibility,batch_runner,cloud
from FusionPromptBridge.execution_policy import validate_reconciliation,validate_read_only


class ImprovementTests(unittest.TestCase):
    def fixture(self):
        helper=k1_fixture.K1Tests();self.addCleanup(helper.doCleanups)
        f,s,task=helper.budget_fixture()
        request=dict(operation_id='interrupted-source',document_id='doc',component_token='carrier',units='mm',
                     script='def run(ctx): return None',checkpoint_before=False,validate_after=True)
        job=s.submit(request);claimed=s.claim('fixture')
        guard=maintainability.Guard(s,f.design,f.selection(),task,'doc',claimed['operation_id'])
        s.recover()
        ctx=NS(store=s,design=f.design,document=f.doc,selection=f.selection(),guard=lambda:None,
               request={'document_id':'doc','mode':'reconcile'})
        return f,s,task,guard,job,ctx

    def test_runtime_mismatch_missing_old_and_same_version_different_build(self):
        current=compatibility.identity()
        compatibility.require_match(dict(current,bridge_path='different machine'))
        for bad in (None,{},dict(current,runtime='0.7.0'),dict(current,build_sha256='old-build')):
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'MCP_RUNTIME_MISMATCH'):
                compatibility.require_match(bad)

    def test_transport_preflight_prevents_mutation_to_old_bridge(self):
        import bridge_client
        with patch.object(bridge_client,'require_compatible_bridge',side_effect=ValueError('MCP_RUNTIME_MISMATCH')):
            with self.assertRaisesRegex(ValueError,'MCP_RUNTIME_MISMATCH'):
                bridge_client.call('new_design')

    def test_real_file_transport_handshake_accepts_match_and_blocks_same_version_mismatch(self):
        import bridge_client
        for compatible in (True,False):
            with self.subTest(compatible=compatible),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);seen=[];errors=[]
                def worker():
                    try:
                        until=time.monotonic()+2
                        while time.monotonic()<until:
                            for path in root.glob('*.request'):
                                payload=json.loads(path.read_text());seen.append(payload['operation'])
                                if payload['operation']=='runtime_identity':
                                    result=dict(compatibility.identity())
                                    if not compatible:result['build_sha256']='other-build'
                                else:
                                    compatibility.require_match(payload['caller']);result={'created':'disposable'}
                                bridge_client.atomic_json(path.with_suffix('.response'),{'ok':True,'result':result});path.unlink()
                                if len(seen)==2 or not compatible:return
                            time.sleep(.005)
                    except Exception as exc:errors.append(str(exc))
                thread=threading.Thread(target=worker);thread.start()
                try:
                    if compatible:self.assertEqual(bridge_client.call('new_design',root=root,timeout=1),{'created':'disposable'})
                    else:
                        with self.assertRaisesRegex(ValueError,'MCP_RUNTIME_MISMATCH'):bridge_client.call('new_design',root=root,timeout=1)
                finally:thread.join(3)
                self.assertFalse(errors);self.assertEqual(seen,['runtime_identity','new_design'] if compatible else ['runtime_identity'])

    def test_legacy_queued_model_job_rejected_before_edit_token_or_script(self):
        f,s,task,guard,job,ctx=self.fixture()
        request=dict(operation_id='legacy',document_id='doc',component_token='carrier',units='mm',
                     script='def run(ctx): raise AssertionError("must not run")',checkpoint_before=False,validate_after=False)
        queued=s.submit(request);claimed=s.claim('fixture');claimed['request'].pop('_caller')
        with patch.object(cloud,'require_edit',side_effect=AssertionError('token consumed')):
            batch_runner.execute_job(s,claimed,f.app,lambda:f.design,lambda:'doc')
        self.assertIn('MCP_RUNTIME_MISMATCH',s.result(queued['job_id'])['result']['message'])

    def test_reconciliation_counts_growth_preserves_attempts_and_requires_strategy_change(self):
        f,s,task,guard,job,ctx=self.fixture()
        extra=f.feature('added',0);f.part.features.values.append(extra);f.refs['added']=extra
        proposal=recovery.inspect(ctx,task['issue_id'],job['job_id'])
        self.assertFalse(proposal['blockers']);self.assertEqual(proposal['growth']['features'],1)
        answer=recovery.acknowledge(ctx,task['issue_id'],proposal['observation_id'],'Observed retained native work',job['job_id'])
        self.assertEqual(answer['status'],'acknowledged_not_qualified')
        self.assertEqual(s.result(job['job_id'])['status'],'interrupted')
        with self.assertRaisesRegex(ValueError,'changed strategy'):
            maintainability.Guard(s,f.design,f.selection(),task,'doc','same-strategy')
        revised=copy.deepcopy(task);revised['authoring']['strategy_revision']='B'
        continued=maintainability.Guard(s,f.design,f.selection(),revised,'doc','new-hypothesis')
        self.assertEqual(continued.status['attempt'],2)
        self.assertEqual(continued.finish(True)['cumulative_growth']['features'],1)
        with self.assertRaisesRegex(ValueError,'no interrupted'):
            recovery.acknowledge(ctx,task['issue_id'],proposal['observation_id'],'No replay',job['job_id'])

    def test_stale_observation_and_protected_change_are_blocked(self):
        f,s,task,guard,job,ctx=self.fixture()
        proposal=recovery.inspect(ctx,task['issue_id'],job['job_id'])
        f.part.revisionId='changed'
        with self.assertRaisesRegex(ValueError,'Stale authoring'):
            recovery.acknowledge(ctx,task['issue_id'],proposal['observation_id'],'Old observation',job['job_id'])
        f.supplier.revisionId='foreign-change'
        current=recovery.inspect(ctx,task['issue_id'],job['job_id'])
        self.assertTrue(any('protected_component_changed' in b for b in current['blockers']))

    def test_removed_history_wrong_document_and_live_job_cannot_be_acknowledged(self):
        f,s,task,guard,job,ctx=self.fixture()
        ctx.request['document_id']='other'
        with self.assertRaisesRegex(ValueError,'another document'):recovery.inspect(ctx,task['issue_id'],job['job_id'])
        ctx.request['document_id']='doc';f.part.features.values.clear()
        proposal=recovery.inspect(ctx,task['issue_id'],job['job_id'])
        self.assertIn('history_removed_or_unresolvable',proposal['blockers'])
        with self.assertRaisesRegex(ValueError,'blocked'):
            recovery.acknowledge(ctx,task['issue_id'],proposal['observation_id'],'Missing source',job['job_id'])
        with s.connect() as db:db.execute("UPDATE jobs SET status='running' WHERE job_id=?",(job['job_id'],))
        with self.assertRaisesRegex(ValueError,'terminal'):recovery.inspect(ctx,task['issue_id'],job['job_id'])

    def test_reconciliation_grammar_is_literal_ledger_only(self):
        validate_reconciliation(ast.parse('def run(ctx): return ctx.acknowledge_authoring("issue", "hash", "note")'))
        validate_read_only(ast.parse('def run(ctx): return ctx.reconcile_authoring("issue", "job")'))
        for source in ('def run(ctx): return ctx.design.computeAll()',
                       'def run(ctx):\n import os\n return ctx.acknowledge_authoring("i","h","n")',
                       'def run(ctx): return [ctx.acknowledge_authoring("i","h","n")]'):
            with self.assertRaises(ValueError):validate_reconciliation(ast.parse(source))

    def test_foreign_parameter_and_legacy_baseline_remain_blocked(self):
        from test_advanced import Node
        f,s,task,guard,job,ctx=self.fixture()
        f.design.allParameters.values.append(Node(name='foreign',expression='2 mm'))
        proposal=recovery.inspect(ctx,task['issue_id'],job['job_id'])
        self.assertIn('foreign_parameter_change:foreign',proposal['blockers'])
        with s.connect() as db:
            row=db.execute('SELECT record FROM authoring_issues WHERE issue_id=?',(task['issue_id'],)).fetchone()
            record=json.loads(row[0]);record.pop('attempt_snapshot')
            db.execute('UPDATE authoring_issues SET record=? WHERE issue_id=?',(json.dumps(record),task['issue_id']))
        with self.assertRaisesRegex(ValueError,'Legacy ledger'):recovery.inspect(ctx,task['issue_id'],job['job_id'])

    def test_acknowledgement_does_not_reset_exhausted_budget(self):
        f,s,task,guard,job,ctx=self.fixture()
        with s.connect() as db:
            row=db.execute('SELECT record FROM authoring_issues WHERE issue_id=?',(task['issue_id'],)).fetchone()
            record=json.loads(row[0]);record['attempts']=task['authoring']['max_attempts']
            db.execute('UPDATE authoring_issues SET record=? WHERE issue_id=?',(json.dumps(record),task['issue_id']))
        proposal=recovery.inspect(ctx,task['issue_id'],job['job_id'])
        recovery.acknowledge(ctx,task['issue_id'],proposal['observation_id'],'Observed exhaustion',job['job_id'])
        revised=copy.deepcopy(task);revised['authoring']['strategy_revision']='B'
        with self.assertRaisesRegex(ValueError,'exhausted'):
            maintainability.Guard(s,f.design,f.selection(),revised,'doc','no-reset')

    def test_acknowledgement_dispatch_consumes_writer_token_without_regenerating(self):
        f,s,task,guard,job,ctx=self.fixture()
        proposal=recovery.inspect(ctx,task['issue_id'],job['job_id'])
        token=cloud.inspect_state(f.app,f.design,'doc',writer_id='writer')['edit_token']
        script='def run(ctx): return ctx.acknowledge_authoring('+','.join(repr(x) for x in
            (task['issue_id'],proposal['observation_id'],'Observed state',job['job_id']))+')'
        request=dict(operation_id='ack',document_id='doc',component_token='carrier',units='mm',script=script,
            mode='reconcile',checkpoint_before=False,validate_after=False,scope=f.spec,task=task,edit_token=token)
        ack=s.submit(request)
        with patch.object(f.design,'computeAll',side_effect=AssertionError('Reconciliation regenerated')):
            batch_runner.execute_job(s,s.claim('fixture'),f.app,lambda:f.design,lambda:'doc')
        result=s.result(ack['job_id'])
        self.assertEqual(result['status'],'succeeded',result['result'].get('traceback'))
        self.assertFalse(result['result']['regeneration_performed'])
        self.assertEqual(result['result']['return_value']['status'],'acknowledged_not_qualified')
