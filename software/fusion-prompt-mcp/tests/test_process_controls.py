"""Workflow integration metadata controls; no Fusion/native acceptance claim."""
import copy
import unittest
from unittest.mock import patch

from FusionPromptBridge import compatibility
from FusionPromptBridge.modeling_rules import get_rules
from FusionPromptBridge.process_controls import describe
import test_contract


class ProcessControlTests(unittest.TestCase):
    def capability_call(self, bridge):
        fn = test_contract.ContractTests().registered().tools['fusion_capabilities']
        calls = []
        def observe(operation, arguments):
            calls.append((operation, arguments))
            self.assertEqual(operation, 'runtime_identity')
            return copy.deepcopy(bridge)
        with patch.dict(fn.__globals__, call=observe):
            result = fn()
        self.assertEqual(calls, [('runtime_identity', {})])
        return result

    def test_document_free_match_reports_boundaries_without_claiming_approval(self):
        result = self.capability_call(compatibility.identity())
        self.assertTrue(result['compatible'])
        controls = result['process_controls']
        self.assertTrue(controls['applies_to_loaded_pair'])
        self.assertEqual(controls['rules_version'], get_rules()['rules_version'])
        self.assertEqual(controls['scope_task_schema'], '1.0')
        self.assertEqual(controls['controls']['finite_root_ligament_proof'], 'not_implemented')
        self.assertEqual(controls['controls']['effective_presets_and_emitted_paths'], 'external_adapter_required')
        self.assertFalse(controls['results']['failed_job_authorizes_replay'])
        self.assertFalse(controls['results']['checked_export_is_manufacturing_approval'])

    def test_same_version_foreign_build_does_not_inherit_controls(self):
        bridge = dict(compatibility.identity(), build_sha256='older-or-foreign-build')
        result = self.capability_call(bridge)
        self.assertFalse(result['compatible'])
        self.assertFalse(result['process_controls']['applies_to_loaded_pair'])

    def test_metadata_is_fresh_per_caller(self):
        first = describe()
        first['controls']['finite_root_ligament_proof'] = 'incorrect pass'
        self.assertEqual(describe()['controls']['finite_root_ligament_proof'], 'not_implemented')


if __name__ == '__main__':
    unittest.main()
