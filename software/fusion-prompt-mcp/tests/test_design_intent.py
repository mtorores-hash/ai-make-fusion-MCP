from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_advanced import Node, Collection
from FusionPromptBridge import design_intent as intent

class IntentTests(unittest.TestCase):
    def test_short_functional_edge_is_not_automatically_a_defect(self):
        edge=Node(length=0.01,pointOnEdge=Node(x=1,y=2,z=3))
        body=Node(edges=Collection([edge]),faces=Collection())
        with patch.object(intent.model_tools,'ref',return_value={'name':'retaining shoulder'}):
            result=intent.surface_audit(body,0.2,0.1,0.1,[edge])
        self.assertTrue(result['findings'][0]['intentional'])
        self.assertEqual(result['findings'][0]['location_mm'],[10,20,30])
        self.assertFalse(result['automatic_modifications'])
        self.assertFalse(result['complete_surface_audit'])
    def test_semantic_selector_is_rerun_and_ambiguity_rejected(self):
        attributes={}
        def add(group,name,value): attributes[name]=Node(value=value);return attributes[name]
        body=Node(attributes=Node(add=add,itemByName=lambda group,name:attributes.get(name)))
        design=Node(allComponents=Collection([Node(bRepBodies=Collection([body]))]))
        first=Node();second=Node()
        with patch.object(intent.model_tools,'select',side_effect=[[first],[second],[first,second]]), \
             patch.object(intent.model_tools,'ref',return_value={}):
            intent.tag_geometry(design,body,'washer_seat','face',{'geometry_type':'Plane'})
            self.assertIs(intent.resolve_tag(design,'washer_seat'),second)
            with self.assertRaisesRegex(ValueError,'uniquely'): intent.resolve_tag(design,'washer_seat')
