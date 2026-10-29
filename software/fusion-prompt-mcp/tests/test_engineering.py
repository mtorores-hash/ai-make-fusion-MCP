"""Behavioral engineering fixtures using API doubles; not native-kernel qualification."""
import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from test_advanced import Node, Collection, core, fusion
import test_scoped_workflow
from FusionPromptBridge import batch_runner, engineering, engineering_geometry as geom, manufacturing, recovery, scope, design_intent
from FusionPromptBridge.job_store import Store, load_engineering_report


def point(v):return Node(x=v[0],y=v[1],z=v[2])
def box(low,high):
    return Node('BRepBody',boundingBox=Node(minPoint=point(low),maxPoint=point(high)),
                volume=max(0,high[0]-low[0])*max(0,high[1]-low[1])*max(0,high[2]-low[2]))


def record_metric(name,value):
    path=os.getenv('MCP_ENGINEERING_METRICS')
    if path:
        file=Path(path);data=json.loads(file.read_text()) if file.exists() else {}
        data[name]=value;file.write_text(json.dumps(data,indent=2)+'\n')


class BoxKernel:
    """Exact axis-aligned box arithmetic ONLY. Does not approximate arbitrary BRep."""
    def copy(self,b):return copy.copy(b)
    def createBox(self,spec):
        c,x,y,l,w,h=spec
        return box([c.x-l/2,c.y-w/2,c.z-h/2],[c.x+l/2,c.y+w/2,c.z+h/2])
    def booleanOperation(self,a,b,kind):
        lo=[max(getattr(a.boundingBox.minPoint,k),getattr(b.boundingBox.minPoint,k)) for k in 'xyz']
        hi=[min(getattr(a.boundingBox.maxPoint,k),getattr(b.boundingBox.maxPoint,k)) for k in 'xyz']
        a.volume=box(lo,hi).volume;a.boundingBox=box(lo,hi).boundingBox;return True


class EngineeringTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_scoped_workflow.WorkflowTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        f=self.fixture;self.design=f.design;self.root=f.root;self.app=f.app
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.store=Store(self.temp.name)
        self.spec=dict(f.spec,targets=['root'],members=[f.member('root',f.root)])
        self.ctx=self.context('first')
        self.a=self.body('wallA',[0,0,0],[1,1,1]);self.b=self.body('wallB',[0.02,1,0],[1.02,2,1])
        self.fa=self.face('faceA',self.a,[0,0.5,0.5]);self.fb=self.face('faceB',self.b,[0.02,1.5,0.5])
        self.plan={'version':'1.0','document_id':'fixture','interfaces':{
            'wallA':{'reference':{'token':'faceA'},'protected':True},'wallB':{'reference':{'token':'faceB'}},
            'tool':{'reference':{'token':'wallA'},'envelopes':{'access':{'frame':'world_mm','min_mm':[0,0,0],
                    'max_mm':[5,5,20],'source':'test tool size','geometry_revision':'br1'}}},
            'obstacle':{'reference':{'token':'wallB'}}},'checks':[]}
        self.kernel=BoxKernel()
        for obj,name,value in [(core,'Point3D',Node(create=lambda *v:point(v))),
                               (core,'Vector3D',Node(create=lambda *v:point(v))),
                               (core,'OrientedBoundingBox3D',Node(create=lambda *v:v)),
                               (fusion,'TemporaryBRepManager',Node(get=lambda:self.kernel)),
                               (fusion,'BooleanTypes',Node(IntersectionBooleanType=1))]:
            p=patch.object(obj,name,value,create=True);p.start();self.addCleanup(p.stop)
        self.app.measureManager=Node(measureMinimumDistance=self.measure)
    def context(self,op):
        request=dict(operation_id=op,document_id='fixture',component_token='root',units='mm',
                     script='def run(ctx):\n    return {}',checkpoint_before=False,validate_after=False)
        job=self.store.submit(request);self.store.claim('fixture');job['request']=request
        ctx=batch_runner.Context(self.store,job,self.app,self.design,self.root,lambda:None)
        spec=copy.deepcopy(self.spec);spec['members'][0]['revision']=self.root.revisionId
        ctx.selection=scope.Selection(self.design,spec);return ctx
    def body(self,name,lo,hi):
        b=self.fixture.body(name,self.root);b.boundingBox=box(lo,hi).boundingBox;b.volume=box(lo,hi).volume
        b.faces=Collection();self.root.bRepBodies.add(b);self.fixture.refs[name]=b;return b
    def face(self,name,body,location):
        e=Node('BRepFace',entityToken=name,body=body,isValid=True,area=1,edges=Collection(),
               geometry=Node('Plane',normal=point([1,0,0]),origin=point(location)),pointOnFace=point(location),
               boundingBox=Node(minPoint=point(location),maxPoint=point(location)))
        body.faces.add(e);self.fixture.refs[name]=e;return e
    def measure(self,a,b):
        return Node(value=abs(a.pointOnFace.x-b.pointOnFace.x),positionOne=a.pointOnFace,positionTwo=b.pointOnFace)
    def wall(self):return {'id':'wall','kind':'continuous_wall','interfaces':['wallA','wallB'],
                           'limits':{'step_mm':0.05,'gap_mm':0.05,'normal_angle_deg':0.1}}
    def access(self,operation='screwdriver'):
        return {'id':operation,'kind':'access','operation':operation,'moving':'tool','envelope':'access',
                'obstacles':['obstacle'],'translations_mm':[[0,0,0]],'max_samples':3,'limits':{'max_volume_mm3':0}}
    def test_defects_intent_and_compact_evidence(self):
        self.b.boundingBox=box([0,0,1],[1,1,2]).boundingBox
        self.plan['checks']=[self.wall(),self.access(),self.access('connected_wire')]
        begin=time.perf_counter();summary=engineering.verify(self.ctx,self.plan);latency=time.perf_counter()-begin
        full=load_engineering_report(self.store,self.ctx.job_id)
        self.assertEqual(summary['failed'],['wall','screwdriver','connected_wire'])
        self.assertAlmostEqual(summary['checks'][0]['evidence']['step_mm'],0.2)
        self.assertIn('location_mm',summary['checks'][1]['evidence']['first_failure'])
        # An intentional seam is evaluated against its own dimensional requirement.
        intentional=copy.deepcopy(self.plan);intentional['checks']=[dict(self.wall(),kind='gap',
            limits={'min_mm':0.15,'max_mm':0.25},intent_reason='assembly seam')]
        self.assertEqual(engineering.verify(self.context('intentional'),intentional)['failed'],[])
        press=copy.deepcopy(self.plan);press['interfaces']['solidA']={'reference':{'token':'wallA'}}
        self.b.boundingBox=box([0,0,.9],[1,1,1.9]).boundingBox
        press['checks']=[dict(id='press',kind='intersection',interfaces=['solidA','obstacle'],
                             limits={'max_volume_mm3':101},intent_reason='declared press engagement')]
        accepted=engineering.verify(self.context('press'),press,detail=True)['checks'][0]
        self.assertEqual(accepted['status'],'pass');self.assertGreater(accepted['volume_mm3'],0)
        if os.getenv('MCP_ENGINEERING_METRICS'):
            metrics={'environment':'Python API doubles, axis-aligned box kernel; not real Fusion',
                     'defects_detected':3,'defect_cases':3,'false_positives':0,'intentional_control_cases':2,
                     'batch_context_calls':1,'mcp_transport_calls':'unmeasured','latency_seconds':latency,
                     'summary_bytes':len(json.dumps(summary).encode()),'detail_bytes':len(json.dumps(full).encode()),
                     'native_kernel_cases_executed':0,'diagnostics':summary['diagnostics']}
            Path(os.environ['MCP_ENGINEERING_METRICS']).write_text(json.dumps(metrics,indent=2)+'\n')
    def test_sampling_uncertainty_cancel_and_kernel_failure_stay_honest(self):
        check=self.access();check['translations_mm']=[[100,0,0],[200,0,0]];self.plan['checks']=[check]
        r=engineering.verify(self.ctx,self.plan,detail=True)
        self.assertEqual(r['checks'][0]['status'],'unproven');self.assertIn('between_poses',r['checks'][0]['not_checked'])
        self.plan['checks']=[self.wall()];self.fb.pointOnFace.x=0
        self.plan['interfaces']['wallA']['dimensions']=[dict(name='thickness',nominal_mm=2,lower_deviation_mm=-.1,
            upper_deviation_mm=.1,provenance='assumed',source='temporary assumption',geometry_revision='br1')]
        self.assertEqual(engineering.verify(self.context('assumed'),self.plan)['checks'][0]['status'],'unproven')
        with patch.object(geom,'planar_wall',side_effect=batch_runner.Cancelled('stop')):
            with self.assertRaises(batch_runner.Cancelled):engineering.verify(self.context('cancel'),self.plan)
        with patch.object(geom,'planar_wall',side_effect=RuntimeError('kernel unavailable')):
            self.assertEqual(engineering.verify(self.context('unavailable'),self.plan)['checks'][0]['status'],'unproven')
    def test_reuse_tracks_geometry_placement_parameters_and_corrupt_evidence(self):
        self.plan['checks']=[self.wall()];self.design.allParameters.add(Node(name='width',expression='2 mm'))
        self.plan['interfaces']['wallA']['parameter_names']=['width']
        engineering.verify(self.ctx,self.plan)
        self.fixture.other.revisionId='unrelated-change'
        reused=engineering.verify(self.context('reuse'),self.plan,self.ctx.job_id)
        self.assertEqual(reused['diagnostics']['reused_checks'],1)
        for change in ['body','parameter','placement']:
            if change=='body':self.a.revisionId='br2'
            if change=='parameter':self.design.allParameters.item(0).expression='3 mm'
            if change=='placement':self.fa.assemblyContext=Node(entityToken='occ',transform2=Node(asArray=lambda:[2]*16))
            r=engineering.verify(self.context(change),self.plan,self.ctx.job_id)
            self.assertEqual(r['diagnostics']['reused_checks'],0)
        path=Path(self.ctx.result['engineering_report']['artifact']['path']);path.write_text('{}')
        with self.assertRaises(ValueError):load_engineering_report(self.store,self.ctx.job_id)
    def test_signature_recovery_rejects_ambiguity_and_protected_changes(self):
        attributes={};self.a.attributes=Node(add=lambda g,n,v:attributes.setdefault(n,Node(value=v)),itemByName=lambda g,n:attributes.get(n))
        self.b.attributes=Node(itemByName=lambda g,n:None)
        # Only tagged bodies need attribute support in this isolated double.
        for c in self.design.allComponents.values:
            for b in c.bRepBodies.values:
                if not hasattr(b,'attributes'):b.attributes=Node(itemByName=lambda g,n:None)
        feature=Node(entityToken='deleted-feature',faces=Collection([self.fa]))
        design_intent.tag_geometry(self.design,self.a,'mount','face',{},feature,signature_tolerances={'bounds_mm':.1,'area':2},allow_feature_fallback=True)
        self.fa.area=1.01
        self.assertEqual(design_intent.resolve_tag(self.design,'mount',True)['method'],'signature_fallback_after_stale_feature')
        self.face('duplicate',self.a,[0,.5,.5])
        with self.assertRaises(design_intent.ReferenceFailure) as caught:design_intent.resolve_tag(self.design,'mount')
        self.assertEqual(caught.exception.code,'reference_ambiguous')
        before=engineering.Session(self.ctx,self.plan).protected();self.fa.area=2
        after=engineering.Session(self.ctx,self.plan).protected()
        self.assertEqual(engineering.compare_protected(before,after)['status'],'fail')
        wrong=dict(self.plan,document_id='another-document')
        with self.assertRaises(design_intent.ReferenceFailure) as caught:engineering.Session(self.ctx,wrong)
        self.assertEqual(caught.exception.code,'wrong_document')
        record_metric('reference_and_protection',{'signature_fallback_successes':1,'attempts':1,
                      'ambiguous_matches_rejected':1,'protected_metric_changes_detected':1,'wrong_document_rejected':1})
    def test_interrupted_mutation_records_change_and_never_replays(self):
        self.ctx.checkpoint=Mock(return_value={'path':'test-checkpoint.f3d'});self.ctx.synchronize=Mock()
        self.ctx.result['before_observation']=recovery.observe(self.ctx)
        calls=[]
        def first(ctx):calls.append('first');self.root.revisionId='r2';return {'changed':True}
        recovery.run_stage(self.ctx,'first',first,lambda c:{'status':'pass'},self.plan)
        def broken(ctx):calls.append('broken');self.root.revisionId='r3';raise RuntimeError('simulated disconnect after mutation')
        with self.assertRaises(RuntimeError):recovery.run_stage(self.ctx,'second',broken,lambda c:{'status':'pass'},self.plan)
        self.assertTrue(self.ctx.result['stages']['second']['change_observation']['model_changed'])
        self.store.finish(self.ctx.job_id,'interrupted',self.ctx.result)
        r=recovery.reconcile(self.context('reconcile'),self.ctx.job_id)
        self.assertEqual(calls,['first','broken']);self.assertFalse(r['replayed'])
        self.assertEqual(r['completed_stages_do_not_replay'],['first']);self.assertEqual(r['unresolved_stages'],['second'])
        self.assertEqual(r['protected_interfaces'][0]['status'],'pass')
        with self.assertRaisesRegex(ValueError,'already attempted'):recovery.run_stage(self.ctx,'first',first,lambda c:{'status':'pass'})
        self.assertEqual(calls,['first','broken'])
        record_metric('recovery',{'action_invocations':len(calls),'replayed_mutations':0,
                      'completed_stages_preserved':len(r['completed_stages_do_not_replay']),
                      'unresolved_stages_reported':len(r['unresolved_stages']),
                      'protected_comparisons':[p['status'] for p in r['protected_interfaces']]})
    def test_manufacturing_handoff_rejects_stale_geometry(self):
        path=Path(self.temp.name)/'part.step';path.write_text('API-double export bytes')
        entry=dict(self.ctx.artifact(path),geometry_identity=manufacturing.identity(self.ctx,self.a))
        part=dict(print_orientation={'frame':'native_component','x_axis':[1,0,0],'z_axis':[0,0,1]},
                  bed_contact_face='wallA',protected_interfaces=['wallA'],allowed_support_faces=[],support_exceptions=[],
                  overhangs=[],bridges=[],access_constraints=[],geometry_review={'status':'unproven','source':'fixture declaration'})
        spec={'version':'1.0','interface_plan':self.plan,'parts':{str(path):part}}
        report=manufacturing.handoff(self.ctx,[entry],spec)
        self.assertEqual(report['manufacturing_readiness'],'unproven');self.assertEqual(report['slicer_inspection'],'required')
        self.a.revisionId='changed-after-export'
        with self.assertRaisesRegex(ValueError,'Stale exported'):manufacturing.handoff(self.ctx,[entry],spec)

    def test_smoothness_samples_detect_discontinuity_but_do_not_certify_g2(self):
        edge=Node('BRepEdge',entityToken='shared',evaluator=Node(getParameterExtents=lambda:(True,0,1),
            getPointAtParameter=lambda t:(True,point([0,t,0]))))
        for face in (self.fa,self.fb):
            face.edges=Collection([edge]);face.evaluator=Node(getNormalAtPoint=lambda p:(True,point([1,0,0])),
                getParameterAtPoint=lambda p:(True,p),getCurvature=lambda p:(True,point([0,1,0]),0,0))
        check=dict(id='smooth',kind='G2',interfaces=['wallA','wallB'],samples=3,
                   limits={'normal_angle_deg':1,'curvature_per_mm':.01})
        self.plan['checks']=[check]
        self.assertEqual(engineering.verify(self.ctx,self.plan)['checks'][0]['status'],'unproven')
        self.fb.evaluator.getNormalAtPoint=lambda p:(True,point([0,1,0]))
        report=engineering.verify(self.context('hard-edge'),self.plan)
        self.assertEqual(report['checks'][0]['status'],'fail')
        self.assertEqual(report['checks'][0]['evidence']['first_failure']['normal_angle_deg'],90)

    def test_required_engineering_failure_blocks_export_before_file_creation(self):
        self.plan['checks']=[self.wall()]
        self.ctx.synchronize=Mock();self.ctx.require_hygiene=Mock(return_value={'automated_checks_passed':True})
        self.ctx.export=Mock()
        # Exporting a body avoids irrelevant fixture child components.
        with self.assertRaisesRegex(RuntimeError,'engineering checks'):
            self.ctx.export_checked('blocked.step',self.a,manual_review_note='test',engineering_plan=self.plan)
        self.ctx.export.assert_not_called()

    def test_known_dependency_gap_downgrades_clear_result(self):
        self.plan['checks']=[self.wall()];self.fb.pointOnFace.x=0
        self.root.joints=Collection([Node(occurrenceOne=Node(component=self.root),occurrenceTwo=self.fixture.o2)])
        report=engineering.verify(self.ctx,self.plan)
        self.assertEqual(report['checks'][0]['status'],'pass')
        self.assertEqual(report['conclusions']['geometric_quality'],'unproven')
        self.assertTrue(report['dependency_scope_gaps'])


if __name__=='__main__':unittest.main()
