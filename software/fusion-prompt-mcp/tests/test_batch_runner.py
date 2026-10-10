"""Batch engine integration with API doubles. These are not Fusion kernel tests."""
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_advanced import Node, Cast, Collection, core, fusion
fusion.Component=Cast('Component')
fusion.RevoluteJointMotion=Cast('RevoluteJointMotion')
fusion.CylindricalJointMotion=Cast('CylindricalJointMotion')
fusion.SliderJointMotion=Cast('SliderJointMotion')
core.Line3D=Cast('Line3D')
core.Point3D=Node(create=lambda x,y,z:Node(x=x,y=y,z=z))
core.CustomEventHandler=object
from FusionPromptBridge.job_store import Store
from FusionPromptBridge import batch_runner as runner, model_tools

class BatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.store=Store(self.tmp.name)
        runner.cloud.reset();self.addCleanup(runner.cloud.reset)
        fusion.FeatureHealthStates=Node(HealthyFeatureHealthState=0,WarningFeatureHealthState=1,ErrorFeatureHealthState=2)
        self.target=Node('Component',entityToken='root',name='Root',revisionId='r1',isValid=True,
                         features=Collection(),joints=Collection(),asBuiltJoints=Collection(),allOccurrences=Collection())
        self.design=Node(findEntityByToken=lambda t:[self.target] if t=='root' else [],
                         rootComponent=self.target,computeAll=lambda:True,
                         allComponents=Collection([self.target]),allParameters=Collection())
        self.app=Node(activeDocument=Node(name='Test',isModified=False,isSaved=False,allDocumentReferences=Collection()))
        self.req=dict(operation_id='batch',document_id='doc',component_token='root',units='mm',
                      script='def run(ctx):\n    ctx.progress(0.5,"half")\n    print("hello")\n    ctx.record("diameter_mm",12)\n    return {"ok":True}',
                      checkpoint_before=False,validate_after=True)
    def run_job(self,request=None,doc='doc'):
        request=dict(request or self.req)
        if 'edit_token' not in request:
            request['edit_token']=runner.cloud.inspect_state(self.app,self.design,'doc')['edit_token']
        j=self.store.submit(request); claimed=self.store.claim('owner')
        with patch.object(runner,'inventory',return_value=[]), patch.object(runner.Context,'validate',return_value={'feature_errors':[]}):
            runner.execute_job(self.store,claimed,self.app,lambda:self.design,lambda:doc)
        return self.store.result(j['job_id'])
    def test_success_has_structured_results_and_stdout(self):
        r=self.run_job(); self.assertEqual(r['status'],'succeeded')
        self.assertEqual(r['result']['measurements']['diameter_mm'],12)
        self.assertIn('hello',r['result']['stdout'])
        self.assertEqual(r['result']['return_value'],{'ok':True})
    def test_missing_edit_token_blocks_module_execution(self):
        r=self.run_job(dict(self.req,edit_token=''))
        self.assertEqual(r['status'],'failed')
        self.assertIn('edit_token',r['result']['message'])
        self.assertEqual(r['result']['measurements'],{})
    def test_user_edit_between_inspection_and_execution_blocks_batch(self):
        token=runner.cloud.inspect_state(self.app,self.design,'doc')['edit_token']
        self.design.allComponents.item(0).revisionId='manual-change'
        r=self.run_job(dict(self.req,edit_token=token))
        self.assertEqual(r['status'],'failed')
        self.assertIn('changed since inspection',r['result']['message'])
    def test_wrong_document_rejected_before_script(self):
        r=self.run_job(doc='other'); self.assertEqual(r['status'],'failed')
        self.assertIn('Active document ID changed',r['result']['traceback'])
        self.assertEqual(r['result']['measurements'],{})
    def test_wrong_component_rejected(self):
        r=self.run_job(dict(self.req,component_token='missing'))
        self.assertEqual(r['status'],'failed'); self.assertEqual(r['result']['measurements'],{})
    def test_checkpoint_failure_prevents_module_and_run_execution(self):
        req=dict(self.req,checkpoint_before=True,script='ctx.record("module_executed",True)\ndef run(ctx): return 1')
        with patch.object(runner.Context,'checkpoint',side_effect=RuntimeError('archive failed')):
            r=self.run_job(req)
        self.assertEqual(r['status'],'failed'); self.assertEqual(r['result']['measurements'],{})
        self.assertIn('archive failed',r['result']['traceback'])
    def test_complete_traceback_and_partial_measurements(self):
        req=dict(self.req,script='def run(ctx):\n    ctx.record("done",1)\n    raise ValueError("cad failed")')
        r=self.run_job(req)
        self.assertEqual(r['result']['measurements']['done'],1)
        self.assertIn('ValueError: cad failed',r['result']['traceback'])
        self.assertIn('line 3',r['result']['traceback']); self.assertTrue(r['result']['partial_changes_possible'])
    def test_cooperative_cancellation(self):
        req=dict(self.req,script='def run(ctx):\n    ctx.store.cancel(ctx.job_id)\n    ctx.progress(0.5,"stop here")\n    ctx.record("wrong",1)')
        r=self.run_job(req)
        self.assertEqual(r['status'],'cancelled'); self.assertNotIn('wrong',r['result']['measurements'])
    def test_non_json_return_is_a_clear_failure(self):
        r=self.run_job(dict(self.req,script='def run(ctx): return object()'))
        self.assertEqual(r['status'],'failed'); self.assertIn('not JSON serializable',r['result']['traceback'])
    def test_script_runs_on_calling_thread(self):
        req=dict(self.req,script='def run(ctx):\n    import threading\n    return threading.get_ident()')
        r=self.run_job(req); self.assertEqual(r['result']['return_value'],threading.get_ident())
    def context(self):
        j=self.store.submit(self.req); claimed=self.store.claim('owner')
        return runner.Context(self.store,claimed,self.app,self.design,self.target,lambda:None)
    def test_motion_restores_pose_after_check_error(self):
        ctx=self.context(); joint=Node(jointMotion=Node('RevoluteJointMotion',rotationValue=0.25))
        self.design.unitsManager=Node(convert=lambda x,a,b:x)
        with patch.object(ctx,'minimum_distance',side_effect=RuntimeError('measurement failed')):
            with self.assertRaisesRegex(RuntimeError,'measurement failed'):
                matrix=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
                occ=Node(transform2=Node(asArray=lambda:matrix))
                self.design.rootComponent.allOccurrences=Collection([occ])
                with patch.object(runner.model_tools,'ref',return_value={}):
                    ctx.sample_motion(joint,[0.5,1.0],[('a','b')],expected_world=lambda p:[(occ,matrix)])
        self.assertEqual(joint.jointMotion.rotationValue,0.25)
    def test_default_mode_keeps_v03_operation_id_digest(self):
        old=self.store.submit(self.req)
        new=self.store.submit(dict(self.req,mode='modeling'))
        self.assertEqual(old['job_id'],new['job_id'])
    def test_read_only_performs_no_regeneration(self):
        from unittest.mock import Mock
        self.design.computeAll=Mock(side_effect=AssertionError('read-only regenerated'))
        for i in range(3):
            r=self.run_job(dict(self.req,operation_id='read'+str(i),mode='read_only',
                                script='def run(ctx): return ctx.validate()'))
            self.assertEqual(r['status'],'succeeded')
        self.design.computeAll.assert_not_called()
    def test_modeling_still_regenerates(self):
        from unittest.mock import Mock
        self.design.computeAll=Mock(return_value=True)
        self.assertEqual(self.run_job()['status'],'succeeded')
        self.design.computeAll.assert_called_once()
    def test_explicit_root_target(self):
        r=self.run_job(dict(self.req,component_token='@root'))
        self.assertEqual(r['status'],'succeeded')
    def test_motion_rejects_stale_transform_even_if_joint_value_changes(self):
        ctx=self.context(); joint=Node(jointMotion=Node('RevoluteJointMotion',rotationValue=0.25))
        self.design.unitsManager=Node(convert=lambda x,a,b:x)
        matrix=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
        expected=list(matrix); expected[3]=1
        occ=Node(transform2=Node(asArray=lambda:matrix))
        self.design.rootComponent.allOccurrences=Collection([occ])
        from unittest.mock import Mock
        with patch.object(runner.adsk,'doEvents',Mock(),create=True), \
             patch.object(ctx,'minimum_distance') as measure:
            with self.assertRaisesRegex(RuntimeError,'unverified'):
                ctx.sample_motion(joint,[1],[('a','b')],expected_world=lambda p:[(occ,expected)])
            measure.assert_not_called()
        self.assertEqual(joint.jointMotion.rotationValue,0.25)
        self.assertTrue(ctx.result['pose_restored'])
    def test_explicit_mm_point_conversion(self):
        ctx=self.context(); p=ctx.point(10,20,30)
        self.assertEqual((p.x,p.y,p.z),(1,2,3))

class GeometryTests(unittest.TestCase):
    def edge(self,x=0):
        g=Node('Line3D',direction=Node(x=0,y=0,z=1))
        b=Node(minPoint=Node(x=x,y=0,z=0),maxPoint=Node(x=x,y=0,z=2))
        return Node('BRepEdge',geometry=g,boundingBox=b,length=2)
    def test_direction_length_and_location(self):
        a=self.edge(0); b=self.edge(1); body=Node(edges=Collection([a,b]))
        result=model_tools.select(body,filters={'parallel_to':[0,0,1],'length_mm':[19.9,20.1],
                                               'at_coordinate_mm':{'x':0}})
        self.assertEqual(result,[a])
    def test_feature_boundary_filter(self):
        a=self.edge(); b=self.edge(); body=Node(edges=Collection([a,b]))
        feature=Node(faces=Collection([Node(edges=Collection([b]))]))
        self.assertEqual(model_tools.select(body,feature=feature),[b])
    def test_unknown_filter_is_not_silently_ignored(self):
        with self.assertRaises(ValueError): model_tools.select(Node(edges=Collection()),filters={'typo':1})
    def test_nonunique_selection_requires_explicit_handling(self):
        with self.assertRaises(ValueError): runner.Context.expect_one([self.edge(),self.edge()])

class EventDispatchTests(unittest.TestCase):
    def test_handler_dispatches_on_calling_thread_and_blocks_reentry(self):
        from FusionPromptBridge import FusionPromptBridge as bridge
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as directory:
            store=Mock(); store.claim.return_value={'job_id':'job','request':{}}
            ids=[]
            def execute(*args):
                ids.append(threading.get_ident())
                bridge.Handler().notify(None)  # Recursive custom event must not execute again.
            with patch.object(bridge,'ROOT',Path(directory)),patch.object(bridge,'_store',store), \
                 patch.object(bridge,'_busy',False), \
                 patch.object(bridge,'_app',Node(userInterface=Node(activeCommand='SelectCommand'))), \
                 patch.object(bridge.batch_runner,'execute_job',side_effect=execute):
                bridge.Handler().notify(None)
                self.assertFalse(bridge._busy)
            self.assertEqual(ids,[threading.get_ident()]); store.claim.assert_called_once()
    def test_handler_waits_for_active_command(self):
        from FusionPromptBridge import FusionPromptBridge as bridge
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as directory:
            store=Mock()
            with patch.object(bridge,'ROOT',Path(directory)),patch.object(bridge,'_store',store), \
                 patch.object(bridge,'_busy',False), \
                 patch.object(bridge,'_app',Node(userInterface=Node(activeCommand='SketchCommand'))):
                bridge.Handler().notify(None)
            store.waiting.assert_called_once(); store.claim.assert_not_called()

if __name__=='__main__': unittest.main()
