"""K1 CAD regression fixtures. API doubles and temporary bytes, no native qualification."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import test_engineering
import test_k1_regressions
from test_advanced import Node, Collection
from FusionPromptBridge import engineering, scope, authoring, maintainability


class CadReviewTests(unittest.TestCase):
    def fixture(self, cls):
        value=cls();value.setUp();self.addCleanup(value.doCleanups);return value

    def probe(self, f):
        f.plan['interfaces']['solid']={'reference':{'token':'wallA'}}
        return {'id':'root-region','kind':'solid_probe','interfaces':['solid'],
                'probe':{'frame':'world_mm','source':'declared junction region, not full load path',
                         'geometry_revision':'br1','min_mm':[0,0,0],'max_mm':[10,10,10]},
                'limits':{'min_fill_fraction':0.9}}

    def test_probe_rejects_thin_region_and_accepts_declared_finite_region(self):
        f=self.fixture(test_engineering.EngineeringTests);check=self.probe(f);f.plan['checks']=[check]
        f.a.boundingBox=test_engineering.box([0,0,0],[.01,1,1]).boundingBox
        row=engineering.verify(f.ctx,f.plan,detail=True)['checks'][0]
        self.assertEqual(row['status'],'fail');self.assertAlmostEqual(row['fill_fraction'],.01)
        self.assertIn('connectivity_to_adjacent_regions',row['not_checked'])
        f.a.boundingBox=test_engineering.box([0,0,0],[1,1,1]).boundingBox;f.a.revisionId='br2'
        check['probe']['geometry_revision']='br2'
        row=engineering.verify(f.context('finite'),f.plan,detail=True)['checks'][0]
        self.assertEqual(row['status'],'pass');self.assertAlmostEqual(row['fill_fraction'],1)
        self.assertEqual(row['evaluation_provenance']['representation'],'Fusion_native_BRep')

    def test_probe_stale_declaration_and_unavailable_kernel_are_unproven(self):
        f=self.fixture(test_engineering.EngineeringTests);check=self.probe(f);f.plan['checks']=[check]
        check['probe']['geometry_revision']='old'
        self.assertEqual(engineering.verify(f.ctx,f.plan)['checks'][0]['status'],'unproven')
        check['probe']['geometry_revision']='br1'
        with patch.object(f.kernel,'booleanOperation',return_value=False):
            self.assertEqual(engineering.verify(f.context('kernel'),f.plan)['checks'][0]['status'],'unproven')
        check['probe']['frame']='component_mm'
        self.assertEqual(engineering.verify(f.context('frame'),f.plan)['checks'][0]['status'],'unproven')

    def test_contradiction_prevents_cached_pass(self):
        f=self.fixture(test_engineering.EngineeringTests);f.fb.pointOnFace.x=0;f.plan['checks']=[f.wall()]
        self.assertEqual(engineering.verify(f.ctx,f.plan)['checks'][0]['status'],'pass')
        f.plan['checks'][0]['contradicted_by']=['exact-mesh-inspection-17']
        result=engineering.verify(f.context('contradicted'),f.plan,f.ctx.job_id)
        self.assertEqual(result['checks'][0]['status'],'unproven')
        self.assertEqual(result['diagnostics']['reused_checks'],0)

    def test_appearance_requires_views_hashes_freshness_and_review(self):
        f=self.fixture(test_engineering.EngineeringTests)
        with tempfile.TemporaryDirectory() as tmp:
            image=Path(tmp)/'front.png';image.write_bytes(b'fixture capture bytes, not an actual image')
            spec=copy.deepcopy(f.spec);spec['dependency_review']='complete'
            spec['required_checks']=[{'id':'appearance','kind':'appearance','members':['root'],'views':['front','corner']}]
            record={'id':'appearance','status':'pass','source':'review-1','reviewer':'design-reviewer',
                    'decision_note':'Declared views inspected against appearance requirement',
                    'revisions':{'root':f.root.revisionId},'captures':[
                        {'view':v,'path':str(image),'sha256':hashlib.sha256(image.read_bytes()).hexdigest()}
                        for v in ('front','corner')]}
            spec['evidence']=[record]
            def result():return scope.evidence(scope.Selection(f.design,spec))[0][0]['status']
            self.assertEqual(result(),'pass')
            record['captures'].pop();self.assertEqual(result(),'unproven')
            record['captures'].append(dict(record['captures'][0],view='corner'))
            image.write_bytes(b'overwritten');self.assertEqual(result(),'unproven')
            for c in record['captures']:c['sha256']=hashlib.sha256(image.read_bytes()).hexdigest()
            record['revisions']['root']='old';self.assertEqual(result(),'unproven')
            record['revisions']['root']=f.root.revisionId;record['contradicted_by']=['owner-reported-appearance-fail']
            self.assertEqual(result(),'unproven')
            record.pop('contradicted_by');record.pop('decision_note');self.assertEqual(result(),'unproven')

    def test_checked_export_blocks_missing_required_evidence_before_writing(self):
        f=self.fixture(test_engineering.EngineeringTests);ctx=f.ctx
        ctx.synchronize=Mock();ctx.export=Mock()
        report={'feature_errors':[],'inspection_gaps':[],'evidence_status':'unproven'}
        with patch.object(scope,'health_report',return_value=report):
            with self.assertRaisesRegex(RuntimeError,'required evidence'):
                ctx.export_checked('part.step',entity=f.a,manual_review_note='fixture')
        ctx.export.assert_not_called()

    def parameter_fixture(self):
        f=self.fixture(test_k1_regressions.K1Tests)
        native,store,task=f.budget_fixture()
        task['allowed_parameter_names']=['width','height']
        task['authoring']['max_new_features']=0
        guard=maintainability.Guard(store,native.design,native.selection(),task,'doc','parameter-edit')
        parameters=Collection([Node(name='width',expression='2 mm',unit='mm'),Node(name='height',expression='3 mm',unit='mm')])
        parameters.itemByName=lambda name:next((p for p in parameters.values if p.name==name),None)
        native.design.userParameters=parameters;native.design.allParameters=parameters
        native.design.unitsManager=Node(isValidExpression=lambda value,unit:value.endswith(' mm'))
        ctx=Node(read_only=False,boundary=scope.EditBoundary(native.design,native.selection(),task,native.part),
                 authoring=guard,design=native.design,selection=native.selection(),check_cancel=Mock(),
                 operation=lambda *a,**k:__import__('contextlib').nullcontext(),synchronize=Mock(),
                 record=lambda name,value:value)
        return native,guard,ctx,parameters

    def test_parameter_edit_preflights_entire_delta_and_preserves_history(self):
        native,guard,ctx,parameters=self.parameter_fixture()
        with self.assertRaisesRegex(ValueError,'Invalid expression'):
            authoring.edit_parameters(ctx,{'width':'4 mm','height':'bad units'})
        self.assertEqual(parameters.itemByName('width').expression,'2 mm')
        value=authoring.edit_parameters(ctx,{'width':'4 mm'})
        self.assertTrue(value['history_preserved']);self.assertEqual(parameters.itemByName('width').expression,'4 mm')
        self.assertEqual(guard.finish(True)['growth'],{'features':0,'sketches':0})

    def test_parameter_route_requires_budget_and_permission_and_detects_history_growth(self):
        native,guard,ctx,parameters=self.parameter_fixture()
        ctx.authoring=None
        with self.assertRaisesRegex(ValueError,'adopted'):authoring.edit_parameters(ctx,{'width':'4 mm'})
        ctx.authoring=guard
        with self.assertRaisesRegex(ValueError,'permitted'):authoring.edit_parameters(ctx,{'outside':'4 mm'})
        ctx.synchronize=lambda:native.part.features.values.append(native.feature('unexpected',0))
        with self.assertRaisesRegex(RuntimeError,'history'):authoring.edit_parameters(ctx,{'width':'4 mm'})
        self.assertEqual(guard.finish(False)['status'],'fail')


if __name__=='__main__':unittest.main()
