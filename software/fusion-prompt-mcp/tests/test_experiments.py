"""Disposable-document lifecycle doubles; real F3D import remains a live gate."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_advanced import Collection, Node
from FusionPromptBridge import experiments

class ExperimentTests(unittest.TestCase):
    def test_rejected_candidate_closes_without_saving_and_keeps_source(self):
        self.run_case(200,False)
    def test_accepted_candidate_exports_only_after_guards(self):
        self.run_case(101,True)
    def test_callback_error_recovers_source(self):
        self.run_case(101,False,fail=True)
    def run_case(self,volume,accepted,fail=False):
        with tempfile.TemporaryDirectory() as folder:
            app=Node()
            source=Node(isValid=True,allDocumentReferences=Collection())
            candidate=Node(isValid=True,products=Node(itemByProductType=lambda _:Node(rootComponent='candidate_root')))
            def activate(doc): app.activeDocument=doc;return True
            source.activate=lambda:activate(source)
            candidate.activate=lambda:activate(candidate)
            candidate.close=Mock(return_value=True)
            app.importManager=Node(createFusionArchiveImportOptions=lambda p:p,importToNewDocument=lambda _:candidate)
            app.activeViewport=Node(camera=Node())
            app.activeDocument=source
            ctx=Node(read_only=False,document=source,design='source_design',target='source_target',
                     guard=lambda:None,app=app,synchronize=Mock(),checkpoint=Mock(return_value={'path':'source.f3d'}),
                     record=Mock(),warn=Mock(),result={'files':[]},export=Mock(return_value={'path':folder+'/accepted.f3d'}))
            before=dict(body_count=1,all_solid=True,all_valid=True,volume_mm3=100,
                        envelope_mm=[0,0,0,10,10,10],feature_errors=[],protected={})
            after=dict(before,volume_mm3=volume)
            def build(c):
                self.assertIs(c.document,candidate)
                if fail: raise RuntimeError('kernel rejected feature')
            with patch.object(experiments.adsk.fusion,'Design',Node(cast=lambda d:d),create=True), \
                 patch.object(experiments,'snapshot',side_effect=[before,before,after]):
                report=experiments.try_feature(ctx,'heal',build,lambda _:[],
                    dict(expected_body_count=1,max_volume_change_mm3=10,max_envelope_change_mm=0.1),capture=False)
            self.assertEqual(report['accepted'],accepted)
            candidate.close.assert_called_once_with(False)
            self.assertIs(ctx.document,source);self.assertIs(app.activeDocument,source)
            self.assertEqual(ctx.design,'source_design')
            self.assertEqual(ctx.export.call_count,1 if accepted else 0)
            self.assertEqual(before['volume_mm3'],100)
            if not accepted: self.assertTrue(report['reasons'])
