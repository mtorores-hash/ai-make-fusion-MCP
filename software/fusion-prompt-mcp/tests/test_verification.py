"""Synthetic policy fixtures, not live CAD or physical printing evidence."""
import ast
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from FusionPromptBridge import verification as v
from FusionPromptBridge.execution_policy import validate_read_only

class PolicyTests(unittest.TestCase):
    def test_nominal_clearance_fails_tolerance_and_preserves_provisional(self):
        r=v.clearance_budget('arm/button',0.35,[dict(name='printed roof',lower_mm=-0.4,upper_mm=0.2,
                          provenance='fixture assumption',status='provisional')])
        self.assertGreater(r['nominal_margin_mm'],0)
        self.assertLess(r['worst_case_margin_mm'],0)
        self.assertFalse(r['passes_bounds']); self.assertTrue(r['provisional'])
    def test_radial_and_diametral_not_silently_converted(self):
        for kind in ('radial','diametral','axial'):
            r=v.clearance_budget('fixture',1,[dict(name='hardware',lower_mm=-0.1,upper_mm=0.2,
                              provenance='drawing',status='specified')],kind=kind)
            self.assertEqual(r['kind'],kind);self.assertAlmostEqual(r['worst_case_margin_mm'],0.9)
    def test_bad_bounds_and_nan_rejected(self):
        with self.assertRaises(ValueError): v.finite(float('nan'))
        with self.assertRaises(ValueError): v.clearance_budget('x',1,[dict(name='x',lower_mm=1,upper_mm=2)])
    def snapshot(self):
        return dict(body_count=1,all_solid=True,all_valid=True,volume_mm3=100,
                    envelope_mm=[0,0,0,10,10,10],feature_errors=[],protected={'bore_mm':3})
    def rules(self):
        return dict(expected_body_count=1,max_volume_change_mm3=10,max_envelope_change_mm=0.2,
                    protected_metrics={'bore_mm':0.01})
    def test_destructive_heal_rejected_despite_valid_solid(self):
        before=self.snapshot();after=dict(before,volume_mm3=200)
        r=v.geometry_delta(before,after,self.rules())
        self.assertFalse(r['accepted']);self.assertIn('volume_change',r['reasons'])
        self.assertEqual(before['volume_mm3'],100)
    def test_lip_and_protected_bore_rejected(self):
        before=self.snapshot();after=dict(before,envelope_mm=[0,0,0,11,10,10],protected={'bore_mm':4})
        r=v.geometry_delta(before,after,self.rules())
        self.assertIn('envelope_change',r['reasons']);self.assertIn('protected:bore_mm',r['reasons'])
    def test_body_count_and_invalid_solid_rejected(self):
        before=self.snapshot();after=dict(before,body_count=2,all_valid=False)
        self.assertEqual(v.geometry_delta(before,after,self.rules())['reasons'],['body_count','solid_validity'])
    def test_small_guarded_edit_accepted(self):
        before=self.snapshot();after=dict(before,volume_mm3=101)
        self.assertTrue(v.geometry_delta(before,after,self.rules())['accepted'])
    def test_broadphase_does_not_reject_touch_or_overlap(self):
        box=lambda lo,hi:dict(min_mm=[lo]*3,max_mm=[hi]*3)
        self.assertFalse(v.separated_boxes(box(0,1),box(1,2)))
        self.assertFalse(v.separated_boxes(box(0,2),box(1,3)))
        self.assertTrue(v.separated_boxes(box(0,1),box(2,3)))
    def test_refinement_detects_narrow_collision_and_reports_limits(self):
        def evaluate(p):
            return dict(clearance_mm=max(abs(p-0.375)-0.01,0),collision=0.365<=p<=0.385)
        r=v.adaptive_samples([0,1],evaluate,near_contact_mm=0.3,max_depth=5)
        self.assertTrue(any(x['collision'] for x in r['samples']))
        self.assertFalse(r['continuous_collision_proof']);self.assertTrue(r['unresolved_intervals'])
    def test_refinement_budget_respected(self):
        r=v.adaptive_samples([0,1],lambda p:dict(clearance_mm=0,collision=False),1,12,3)
        self.assertEqual(r['sample_count'],3)
        self.assertTrue(all(x['reason']=='sample_budget' for x in r['unresolved_intervals']))
    def test_stale_exports_and_calculations_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'part.stl';p.write_bytes(b'fixture')
            e=dict(path=str(p),sha256=v.file_hash(p),model_revision='new')
            c=dict(name='bounds',model_revision='new',passed=True,evidence='measured')
            m=v.build_manifest('new',[e],[c]);v.validate_manifest(m,'new')
            with self.assertRaisesRegex(ValueError,'Stale artifact'): v.build_manifest('new',[dict(e,model_revision='old')],[c])
            with self.assertRaisesRegex(ValueError,'Stale check'): v.build_manifest('new',[e],[dict(c,model_revision='old')])
            p.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'hash changed'): v.validate_manifest(m,'new')
    def test_readonly_grammar_accepts_queries(self):
        validate_read_only(ast.parse('def run(ctx): return {"a":ctx.inspect(False),"b":ctx.capture("v.png",1920,1080)}'))
    def test_readonly_grammar_rejects_mutation_and_escapes(self):
        for code in ['def run(ctx): return ctx.design.computeAll()',
                     'def run(ctx): return ctx.parameter("a","3 mm")',
                     'def run(ctx): return ctx.inspect(ctx.design)',
                     'import os\ndef run(ctx): return 1',
                     'def run(ctx=print("bad")): return 1',
                     '@print("bad")\ndef run(ctx): return 1',
                     'def run(ctx):\n ctx.design=None\n return 1',
                     'def run(ctx): return ctx.__getattribute__("design")',
                     'def run(ctx): return [ctx.inspect() for x in [1]]']:
            with self.subTest(code=code),self.assertRaises(ValueError): validate_read_only(ast.parse(code))

if __name__=='__main__': unittest.main()
