"""Hygiene rules and API-double tests; not live Fusion model evidence."""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_advanced import Node, Collection, fusion
from FusionPromptBridge import hygiene, batch_runner
from FusionPromptBridge.modeling_rules import get_rules
from FusionPromptBridge.execution_policy import validate_read_only
import ast

class HygieneTests(unittest.TestCase):
    def setUp(self):
        health=Node(HealthyFeatureHealthState=0,WarningFeatureHealthState=1,ErrorFeatureHealthState=2)
        self.addCleanup(patch.stopall)
        patch.object(fusion,'FeatureHealthStates',health,create=True).start()
        patch.object(fusion,'DesignTypes',Node(ParametricDesignType=1),create=True).start()
        self.sketch=self.entity('sk_profile',isFullyConstrained=True,sketchCurves=Collection(),
                                sketchDimensions=Collection(),sketchPoints=Collection())
        self.part=self.component('housing',sketches=Collection([self.sketch]),
                                 bRepBodies=Collection([self.entity('housing_body')]))
        self.root=self.component('Untitled')
        self.param=self.entity('wall',comment='Wall thickness; maintain bore clearance',isFavorite=True,
                               dependentParameters=Collection([Node(name='d1')]))
        self.design=Node(rootComponent=self.root,allComponents=Collection([self.root,self.part]),
                         userParameters=Collection([self.param]),designType=1,computeAll=Mock())
    def entity(self,name,**kwargs):
        return Node(name=name,entityToken=name,healthState=0,errorOrWarningMessage='',**kwargs)
    def component(self,name,**kwargs):
        values={k:Collection() for k in ('bRepBodies','sketches','features','joints','asBuiltJoints',
                                       'constructionPlanes','constructionAxes','constructionPoints')}
        values.update(kwargs)
        return self.entity(name,**values)
    def test_clean_automated_subset_is_not_full_standard_approval(self):
        report=hygiene.audit(self.design)
        self.assertTrue(report['automated_checks_passed'])
        self.assertFalse(report['full_standard_verified'])
        self.assertTrue(report['manual_review_required'])
        self.assertEqual(report['review_count'],0)
        self.design.computeAll.assert_not_called()
    def test_underconstrained_sketch_blocks(self):
        self.sketch.isFullyConstrained=False
        report=hygiene.audit(self.design)
        self.assertIn('SKETCH_CONSTRAINTS',[f['rule_id'] for f in report['findings']])
        with self.assertRaisesRegex(RuntimeError,'gate failed'):hygiene.require(report)
        self.assertFalse(self.sketch.isFullyConstrained) # No silent repair.
    def test_yellow_and_red_states_block(self):
        for state in [1,2]:
            with self.subTest(state=state):
                self.part.features=Collection([self.entity('ext_housing')])
                self.part.features.item(0).healthState=state
                report=hygiene.audit(self.design)
                self.assertFalse(report['automated_checks_passed'])
                self.assertTrue(any(f['rule_id']=='TIMELINE_HEALTH' for f in report['findings']))
    def test_default_names_and_blank_names_block(self):
        for name in ['Sketch15','', '   ']:
            self.sketch.name=name
            report=hygiene.audit(self.design)
            self.assertTrue(any(f['rule_id']=='NAME_REQUIRED' for f in report['findings']))
    def test_prefix_style_is_review_not_automatic_rename(self):
        self.sketch.name='profile'
        report=hygiene.audit(self.design)
        self.assertTrue(report['automated_checks_passed'])
        self.assertEqual(report['review_count'],1)
        self.assertEqual(self.sketch.name,'profile')
    def test_root_single_part_exception_is_reviewable(self):
        self.root.bRepBodies=Collection([self.entity('concept_body')])
        report=hygiene.audit(self.design)
        self.assertTrue(report['automated_checks_passed'])
        self.assertIn('ROOT_BODY',[f['rule_id'] for f in report['findings']])
        with self.assertRaises(RuntimeError):hygiene.require(report,strict_reviews=True)
    def test_large_sketch_and_fixed_spline_are_advisories(self):
        self.sketch.sketchCurves=Collection([Node(isFixed=(i==0)) for i in range(100)])
        report=hygiene.audit(self.design)
        self.assertTrue(report['automated_checks_passed'])
        ids=[f['rule_id'] for f in report['findings']]
        self.assertIn('SKETCH_COMPLEXITY',ids);self.assertIn('FIX_USAGE',ids)
    def test_fixed_origin_is_not_misclassified(self):
        origin=Node(isFixed=True)
        self.sketch.originPoint=origin;self.sketch.sketchPoints=Collection([origin])
        self.assertEqual(hygiene.audit(self.design)['review_count'],0)
    def test_unused_parameter_heuristic_does_not_delete_or_certify(self):
        self.param.dependentParameters=Collection()
        self.param.comment='';self.param.isFavorite=False
        report=hygiene.audit(self.design)
        ids={f['rule_id'] for f in report['findings']}
        self.assertTrue({'PARAMETER_USAGE','PARAMETER_COMMENT','PARAMETER_FAVORITE'}<=ids)
        self.assertEqual(self.design.userParameters.count,1)
    def test_unavailable_api_data_fails_closed(self):
        del self.sketch.isFullyConstrained
        report=hygiene.audit(self.design)
        self.assertFalse(report['inspection_complete'])
        with self.assertRaises(RuntimeError):hygiene.require(report)
    def test_null_constraint_state_is_not_pass(self):
        self.sketch.isFullyConstrained=None
        self.assertFalse(hygiene.audit(self.design)['automated_checks_passed'])
    def test_direct_design_reports_need_for_history_without_conversion(self):
        self.design.designType=0
        self.assertFalse(hygiene.audit(self.design)['automated_checks_passed'])
        self.assertEqual(self.design.designType,0)
    def test_readonly_grammar_accepts_hygiene(self):
        validate_read_only(ast.parse('def run(ctx): return ctx.audit_hygiene()'))
    def context(self):
        ctx=object.__new__(batch_runner.Context)
        ctx.design=self.design;ctx.check_cancel=Mock();ctx.record=Mock()
        ctx.export=Mock(return_value={'path':'part.f3d','sha256':'test'})
        ctx.synchronize=Mock()
        return ctx
    def test_checked_export_stops_before_file_write_on_failed_audit(self):
        self.sketch.isFullyConstrained=False
        ctx=self.context()
        with self.assertRaises(RuntimeError):ctx.export_checked('part.f3d',manual_review_note='Reviewed source references')
        ctx.export.assert_not_called()
        ctx.record.assert_called_once()
    def test_checked_export_requires_manual_note_and_preserves_audit_scope(self):
        ctx=self.context()
        with self.assertRaises(ValueError):ctx.export_checked('part.f3d')
        ctx.export.assert_not_called()
        result=ctx.export_checked('part.f3d',manual_review_note='Reviewed references; parameter test recorded separately')
        ctx.export.assert_called_once_with('part.f3d',None)
        self.assertFalse(result['hygiene']['full_standard_verified'])
        self.assertIn('rules_sha256',result['hygiene'])
    def test_runtime_rules_and_optional_repo_copy_are_identical(self):
        software=Path(__file__).resolve().parents[1]
        repo_copy=software.parents[1]/'docs/modeling-rules.md'
        if repo_copy.is_file():
            self.assertEqual((software/'modeling-rules.md').read_bytes(),repo_copy.read_bytes())
        rules=get_rules()
        self.assertEqual(rules['rules_version'],'1.0.5')
        self.assertEqual(len(rules['sha256']),64)
        self.assertIn('Component first',rules['text'])
    def test_bridge_dispatch_checks_target_document(self):
        from FusionPromptBridge import FusionPromptBridge as bridge
        with patch.object(bridge,'_app',Node(userInterface=Node(activeCommand='SelectCommand'))), \
             patch.object(bridge,'design',return_value=self.design), \
             patch.object(bridge,'design_id',return_value='right'):
            with self.assertRaisesRegex(ValueError,'Active document changed'):
                bridge.execute('audit_hygiene',{'design_id':'wrong'})
            result=bridge.execute('audit_hygiene',{'design_id':'right'})
            self.assertTrue(result['automated_checks_passed'])
        self.design.computeAll.assert_not_called()

if __name__=='__main__':unittest.main()
