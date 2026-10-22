"""Source registration/binding checks only. This does NOT emulate the MCP protocol."""
import ast
import inspect
import json
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from FusionPromptBridge.modeling_rules import get_rules
from FusionPromptBridge.job_store import Store

ROOT=Path(__file__).resolve().parents[1]
class Registration:
    def __init__(self,*a,**k):self.tools={};self.resources={}
    def tool(self):
        def register(fn):self.tools[fn.__name__]=fn;return fn
        return register
    def resource(self,uri):
        def register(fn):self.resources[uri]=fn;return fn
        return register

class ContractTests(unittest.TestCase):
    def test_versions_rules_mirror_and_hash_reuse(self):
        result=get_rules();self.assertEqual(result['rules_version'],'1.3.2')
        self.assertEqual((ROOT/'modeling-rules.md').read_bytes(),(ROOT.parents[1]/'docs/modeling-rules.md').read_bytes())
        self.assertTrue(get_rules(result['sha256'])['unchanged']);self.assertNotIn('text',get_rules(result['sha256']))
        self.assertIn('text',get_rules('old'))
        self.assertEqual(json.loads((ROOT/'FusionPromptBridge/FusionPromptBridge.manifest').read_text())['version'],'0.8.0')
    def registered(self):
        sdk=types.ModuleType('mcp.server.fastmcp');sdk.FastMCP=Registration
        with patch.dict(sys.modules,{'mcp':types.ModuleType('mcp'),'mcp.server':types.ModuleType('mcp.server'),'mcp.server.fastmcp':sdk}):
            return runpy.run_path(str(ROOT/'server.py'))['mcp']
    def test_source_registration_and_new_fields(self):
        mcp=self.registered();self.assertEqual(len(mcp.tools),32)
        for name in ('acquire_edit_token','release_edit_token','reconcile_cloud_job','retire_occurrences'):self.assertIn(name,mcp.tools)
        self.assertFalse(inspect.signature(mcp.tools['inspect_document_state']).parameters['acquire_token'].default)
        for name in ('run_model_script','rectangle_sketch','circle_sketch','extrude','set_parameter','fillet_edges','create_joint'):
            sig=inspect.signature(mcp.tools[name])
            for arg in ('scope','task','accepted_reference_versions'):self.assertIsNone(sig.parameters[arg].default)
        self.assertEqual(mcp.resources['fusion://modeling-rules'](),get_rules()['text'])
    def test_example_request_binds_and_deduplicates_without_fusion(self):
        request=json.loads((ROOT/'examples/scoped-validation.request.json').read_text())
        fn=self.registered().tools['run_model_script'];bound=inspect.signature(fn).bind(**request);bound.apply_defaults()
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp);first=store.submit(bound.arguments);second=store.submit(bound.arguments)
            self.assertEqual(first['job_id'],second['job_id'])
        result=json.loads((ROOT/'examples/scoped-validation.result.json').read_text())
        self.assertEqual(result['status'],'succeeded');self.assertEqual(result['result']['validation']['scope']['mode'],'selected')

if __name__=='__main__':unittest.main()
