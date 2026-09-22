"""Contract tests using a small Fusion double; does not validate Fusion geometry."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock

class Cast:
    def __init__(self, tag): self.tag = tag
    def cast(self, obj): return obj if getattr(obj, 'tag', None) == self.tag else None

class Collection:
    def __init__(self, values=()): self.values = list(values)
    @property
    def count(self): return len(self.values)
    def item(self, i): return self.values[i]
    def add(self, obj): self.values.append(obj)
    def contains(self, obj): return obj in self.values

core = types.SimpleNamespace(
    ValueInput=types.SimpleNamespace(createByString=lambda x: x),
    ObjectCollection=types.SimpleNamespace(create=Collection), Plane=Cast('Plane'))
fusion = types.SimpleNamespace(**{name: Cast(name) for name in
    ('Occurrence', 'BRepEdge', 'BRepFace', 'BRepVertex', 'BRepBody')})
fusion.JointKeyPointTypes = types.SimpleNamespace(CenterKeyPoint=0, StartKeyPoint=1,
                                                 EndKeyPoint=2, MiddleKeyPoint=3)
fusion.JointDirections = types.SimpleNamespace(XAxisJointDirection=0, YAxisJointDirection=1,
                                               ZAxisJointDirection=2)
fusion.JointGeometry = types.SimpleNamespace(createByPlanarFace=lambda *x: x,
    createByCurve=lambda *x: x, createByPoint=lambda *x: x)
adsk = types.ModuleType('adsk'); adsk.core = core; adsk.fusion = fusion
sys.modules['adsk'] = adsk; sys.modules['adsk.core'] = core; sys.modules['adsk.fusion'] = fusion
spec = importlib.util.spec_from_file_location('advanced', Path(__file__).resolve().parents[1] /
                                            'FusionPromptBridge' / 'advanced.py')
advanced = importlib.util.module_from_spec(spec); spec.loader.exec_module(advanced)

class Node:
    def __init__(self, tag='', **kwargs):
        self.tag = tag; self.objectType = tag; self.nativeObject = None
        self.assemblyContext = None
        self.__dict__.update(kwargs)

class AdvancedTests(unittest.TestCase):
    def setUp(self):
        self.refs = {}
        self.root = Node(allOccurrences=Collection())
        self.d = Node(rootComponent=self.root, findEntityByToken=lambda t: self.refs.get(t, []),
            unitsManager=Node(isValidExpression=lambda e,u: e != 'bad',
                              evaluateExpression=lambda e,u: float(e.split()[0]) / 10))
        self.feature = Node(entityToken='feature', name='Feature', healthState='healthy',
                            errorOrWarningMessage='')
        self.inp = Mock()
        self.features = Mock(); self.features.createInput.return_value = self.inp
        self.features.add.return_value = self.feature
        self.component = Node(features=Node(filletFeatures=self.features))
        self.body = Node('BRepBody', parentComponent=self.component)
        self.edge = Node('BRepEdge', entityToken='edge', body=self.body)
        self.refs['edge'] = [self.edge]
        self.fargs = dict(edge_tokens=['edge'], radius='2 mm', tangent_chain=False,
                          rolling_ball=True, name='Round')

    def test_fillet_uses_owning_component_and_expression(self):
        r = advanced.execute('fillet', self.fargs, self.d, None)
        self.assertEqual(r['name'], 'Round')
        args = self.inp.edgeSetInputs.addConstantRadiusEdgeSet.call_args.args
        self.assertEqual(args[1:], ('2 mm', False))
        self.assertEqual(args[0].values, [self.edge])

    def test_negative_radius_rejected_before_creation(self):
        self.fargs['radius'] = '-1 mm'
        with self.assertRaises(ValueError): advanced.execute('fillet', self.fargs, self.d, None)
        self.features.add.assert_not_called()

    def test_mixed_body_edges_rejected(self):
        self.refs['other'] = [Node('BRepEdge', body=Node())]
        self.fargs['edge_tokens'].append('other')
        with self.assertRaises(ValueError): advanced.execute('fillet', self.fargs, self.d, None)
        self.features.add.assert_not_called()

    def test_linked_component_rejected(self):
        self.root.allOccurrences = Collection([Node(component=self.component,isReferencedComponent=True)])
        with self.assertRaises(ValueError): advanced.execute('fillet', self.fargs, self.d, None)

    def test_ambiguous_token_rejected(self):
        self.refs['edge'] = [self.edge, self.edge]
        with self.assertRaises(ValueError): advanced.resolve(self.d, 'edge')

    def test_geometry_requires_correct_occurrence(self):
        face = Node('BRepFace', body=self.body)
        self.refs['face'] = [face]
        with self.assertRaises(ValueError): advanced.geometry(self.d, 'face', '', 'center')
        self.refs['occ'] = [Node('Occurrence', component=Node())]
        with self.assertRaises(ValueError): advanced.geometry(self.d, 'face', 'occ', 'center')

    def joint_setup(self):
        o1=Node('Occurrence', component=self.component, fullPathName='A:1')
        o2=Node('Occurrence', component=Node(), fullPathName='B:1')
        for key,o in [('o1',o1),('o2',o2)]: self.refs[key]=[o]
        for key,o in [('f1',o1),('f2',o2)]:
            face=Node('BRepFace', body=Node(parentComponent=o.component),geometry=Node('Plane'))
            face.createForAssemblyContext=lambda o, f=face: f
            self.refs[key]=[face]
        self.root.joints=self.features
        return dict(occurrence_one='o1',occurrence_two='o2',geometry_one='f1',geometry_two='f2',
                    keypoint_one='center',keypoint_two='center',offset='0 mm',angle='0 deg',
                    flipped=False,axis='Z',kind='revolute',name='Hinge')

    def test_all_joint_motion_dispatch(self):
        a=self.joint_setup()
        for kind,method in [('rigid','setAsRigidJointMotion'),('revolute','setAsRevoluteJointMotion'),
                            ('slider','setAsSliderJointMotion'),('cylindrical','setAsCylindricalJointMotion')]:
            with self.subTest(kind=kind):
                self.inp.reset_mock(); a['kind']=kind
                r=advanced.execute('joint',a,self.d,None)
                getattr(self.inp,method).assert_called_once()
                self.assertEqual(r['name'],'Hinge')

    def test_same_occurrence_alias_rejected(self):
        a=self.joint_setup(); self.refs['alias']=self.refs['o1']; a['occurrence_two']='alias'
        with self.assertRaises(ValueError): advanced.execute('joint',a,self.d,None)
        self.features.add.assert_not_called()

    def test_joint_motion_rejection_does_not_add(self):
        a=self.joint_setup(); self.inp.setAsRevoluteJointMotion.return_value=False
        with self.assertRaises(ValueError): advanced.execute('joint',a,self.d,None)
        self.features.add.assert_not_called()

    def test_ancestor_joint_rejected(self):
        a=self.joint_setup(); self.refs['o2'][0].fullPathName='A:1+B:1'
        with self.assertRaises(ValueError): advanced.execute('joint',a,self.d,None)

if __name__ == '__main__': unittest.main()
