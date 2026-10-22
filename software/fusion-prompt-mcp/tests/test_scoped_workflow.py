"""Caller-contract and execution regressions using API doubles, no native CAD operations."""
import ast
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_advanced import Node,Collection,Cast,core,fusion
from FusionPromptBridge import scope,hygiene,batch_runner,retirement,authoring,experiments,cloud
from FusionPromptBridge.job_store import Store

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        fusion.Component=Cast('Component');fusion.FeatureHealthStates=Node(HealthyFeatureHealthState=0,WarningFeatureHealthState=1,ErrorFeatureHealthState=2)
        fusion.DesignTypes=Node(ParametricDesignType=1)
        self.root=self.comp('root');self.part=self.comp('carrier');self.other=self.comp('other');self.supplier=self.comp('Component1')
        self.part.bRepBodies=Collection([self.body('carrier_body',self.part)])
        self.supplier.bRepBodies=Collection([self.body('Body1',self.supplier)])
        self.o1=self.occ('carrier:1',self.part);self.o2=self.occ('other:1',self.other);self.o3=self.occ('supplier:1',self.supplier)
        self.root.occurrences=self.root.allOccurrences=Collection([self.o1,self.o2,self.o3])
        self.components=[self.root,self.part,self.other,self.supplier]
        self.refs={x.entityToken:x for x in self.components+[self.o1,self.o2,self.o3]}
        for c in self.components:
            for b in c.bRepBodies.values:self.refs[b.entityToken]=b
        self.design=Node(rootComponent=self.root,allComponents=Collection(self.components),allParameters=Collection(),
                         userParameters=Collection(),designType=1,findEntityByToken=lambda t:[self.refs[t]] if t in self.refs else [],computeAll=Mock(return_value=True))
        self.spec={'version':'1.0','mode':'selected','targets':['carrier'],'dependencies':[],
                   'members':[self.member('carrier',self.part)],'parameter_names':[],
                   'required_checks':[],'dependency_review':'complete'}
        self.doc=Node(name='assembly',isModified=False,isSaved=False,allDocumentReferences=Collection())
        self.app=Node(activeDocument=self.doc)
        cloud.reset();self.addCleanup(cloud.reset)
    def comp(self,name):
        c=Node('Component',entityToken=name,name=name,revisionId='r1',isValid=True)
        for attr in ('bRepBodies','meshBodies','sketches','features','joints','asBuiltJoints','constructionPlanes',
                     'constructionAxes','constructionPoints','occurrences','allOccurrences'):setattr(c,attr,Collection())
        return c
    def body(self,name,c):
        return Node('BRepBody',entityToken=name,name=name,revisionId='br1',isValid=True,isSolid=True,parentComponent=c,
                    volume=1,faces=Collection([Node()]),edges=Collection(),
                    boundingBox=Node(minPoint=Node(x=0,y=0,z=0),maxPoint=Node(x=1,y=1,z=1)))
    def occ(self,name,c):
        return Node('Occurrence',entityToken=name,name=name,fullPathName=name,component=c,isValid=True,isDerived=False,
                    isGrounded=False,isReferencedComponent=False,childOccurrences=Collection(),joints=Collection(),
                    asBuiltJoints=Collection(),rigidGroups=Collection(),transform2=Node(asArray=lambda:[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]))
    def member(self,ident,c,role='authored',maturity='working'):
        return dict(id=ident,component_token=c.entityToken,revision=c.revisionId,membership='active',maturity=maturity,role=role)
    def feature(self,name,state=2):return Node(entityToken=name,name=name,healthState=state,errorOrWarningMessage='bad' if state==2 else '',isValid=True)
    def selection(self):return scope.Selection(self.design,self.spec)
    def task(self,allowed=None):
        return dict(version='1.0',task_id='TASK-1',issue_id='ISSUE-1',attempt=1,writer_id='writer',baseline_id='B1',
                    allowed_member_ids=allowed or ['carrier'],frozen_member_ids=[],allowed_parameter_names=[],approval_reference='caller-text')
    def test_default_root_scope_uses_supported_root_sentinel_when_token_is_unresolvable(self):
        self.refs.pop(self.root.entityToken)
        spec=scope.selected(self.design,self.root)
        self.assertEqual(spec['members'][0]['component_token'],'@root')
        spec['dependency_review']='complete'
        selected=scope.Selection(self.design,spec)
        self.assertTrue(selected.contains(self.root,targets=True))
    def test_default_child_scope_preserves_observed_component_token(self):
        spec=scope.selected(self.design,self.part)
        self.assertEqual(spec['members'][0]['component_token'],self.part.entityToken)
        spec['dependency_review']='complete'
        self.assertTrue(scope.Selection(self.design,spec).contains(self.part,targets=True))
    def test_unrelated_supplier_naming_does_not_block_selected_authoring(self):
        report=hygiene.audit(self.design,self.spec)
        self.assertTrue(report['automated_checks_passed']);self.assertEqual(report['counts']['components'],1)
        self.assertEqual(report['scope']['mode'],'selected');self.assertFalse(report['full_standard_verified'])
        self.assertTrue(report['exclusions'])
    def test_relevant_supplier_has_interface_evidence_not_style_override(self):
        self.spec['members'].append(self.member('motor',self.supplier,'purchased'));self.spec['dependencies']=['motor']
        r=hygiene.audit(self.design,self.spec)
        self.assertFalse(r['automated_checks_passed']);self.assertEqual(r['error_count'],0)
        self.spec['evidence']=[dict(id='interface_envelope:motor',status='pass',source='supplier-drawing-rev-A',revisions={'motor':'r1'})]
        r=hygiene.audit(self.design,self.spec)
        self.assertTrue(r['automated_checks_passed']);self.assertEqual(r['not_applicable'][0]['id'],'motor')
    def test_required_missing_failed_and_stale_evidence_never_turns_green(self):
        self.spec['required_checks']=[{'id':'IF1','members':['carrier']}]
        for record in [None,dict(id='IF1',status='fail',source='test',revisions={'carrier':'r1'}),
                       dict(id='IF1',status='pass',source='test',revisions={'carrier':'old'}),
                       dict(id='IF1',status='not_applicable',reason='skip',revisions={'carrier':'r1'})]:
            self.spec['evidence']=[record] if record else []
            self.assertFalse(hygiene.audit(self.design,self.spec)['automated_checks_passed'])
    def test_explicit_nonapplicability_is_not_a_pass_or_override(self):
        self.spec['required_checks']=[dict(id='cosmetic',members=['carrier'],applicable=False,reason='not this milestone')]
        self.spec['evidence']=[dict(id='cosmetic',status='not_applicable',reason='not this milestone',revisions={'carrier':'r1'})]
        r=hygiene.audit(self.design,self.spec);self.assertTrue(r['automated_checks_passed'])
        self.assertEqual(r['evidence'][0]['status'],'not_applicable')
    def test_authored_underconstraint_blocks_relevant_scope(self):
        s=Node(name='sk_fit',entityToken='sk_fit',healthState=0,errorOrWarningMessage='',isFullyConstrained=False,
               sketchCurves=Collection(),sketchDimensions=Collection(),sketchPoints=Collection())
        self.part.sketches=Collection([s]);self.assertFalse(hygiene.audit(self.design,self.spec)['automated_checks_passed'])
    def test_scopes_reject_empty_nonexistent_stale_and_retired(self):
        for change in ['empty','missing','stale','retired']:
            spec=copy.deepcopy(self.spec)
            if change=='empty':spec['targets']=[]
            if change=='missing':spec['members'][0]['component_token']='missing'
            if change=='stale':spec['members'][0]['revision']='old'
            if change=='retired':spec['members'][0]['membership']='retired'
            with self.subTest(change=change),self.assertRaises(ValueError):scope.Selection(self.design,spec)
    def test_shared_component_aliases_not_duplicate_members(self):
        self.refs['alias']=self.part;self.spec['members'].append(dict(self.member('alias',self.part),component_token='alias'))
        with self.assertRaisesRegex(ValueError,'aliases'):self.selection()
    def test_joint_dependency_cannot_be_silently_omitted(self):
        self.root.joints=Collection([Node(occurrenceOne=self.o1,occurrenceTwo=self.o2)])
        self.assertTrue(self.selection().gaps)
    def test_export_rejects_mismatched_and_empty_targets(self):
        sel=self.selection();sel.check_export(self.part)
        with self.assertRaises(ValueError):sel.check_export(self.supplier)
        self.part.bRepBodies=Collection()
        with self.assertRaisesRegex(ValueError,'Empty'):sel.check_export(self.part)
    def test_export_parent_cannot_include_unselected_descendants(self):
        self.spec['members'].append(self.member('root',self.root));self.spec['targets']=['root']
        with self.assertRaisesRegex(ValueError,'unselected descendant'):self.selection().check_export(self.root)
    def test_checked_export_gates_exact_selected_entity(self):
        ctx=object.__new__(batch_runner.Context);ctx.design=self.design;ctx.target=self.part;ctx.selection=self.selection()
        ctx.result={};ctx.check_cancel=Mock();ctx.synchronize=Mock();ctx.record=Mock();ctx.export=Mock(return_value={'path':'part.step'})
        report=ctx.export_checked('part.step',self.part,manual_review_note='Task IF1 review',scope=self.spec)
        self.assertEqual(report['scope']['targets'],['carrier']);self.assertEqual(report['approval_status'],'not_evaluated')
        ctx.export.assert_called_once_with('part.step',self.part)
        with self.assertRaises(ValueError):ctx.export_checked('bad.step',self.supplier,manual_review_note='x',scope=self.spec)
        self.assertEqual(ctx.export.call_count,1)
    def test_old_unrelated_errors_visible_but_do_not_fail_current_part(self):
        self.other.features=Collection([self.feature('old-error')]);baseline=scope.health_snapshot(self.design)
        result=scope.health_report(self.design,self.selection(),baseline)
        self.assertEqual(result['validation_status'],'pass');self.assertEqual(len(result['unrelated_preexisting']),1)
    def test_relevant_old_error_and_new_out_of_scope_damage_fail(self):
        baseline=scope.health_snapshot(self.design)
        self.other.features=Collection([self.feature('new-outside')]);r=scope.health_report(self.design,self.selection(),baseline)
        self.assertEqual(len(r['new_errors']),1);self.assertEqual(r['validation_status'],'fail')
        self.part.features=Collection([self.feature('old-relevant')]);baseline=scope.health_snapshot(self.design)
        self.assertEqual(len(scope.health_report(self.design,self.selection(),baseline)['relevant_preexisting']),1)
    def test_old_unrelated_unknown_is_disclosed_not_assigned_to_task(self):
        del self.other.features;baseline=scope.health_snapshot(self.design)
        r=scope.health_report(self.design,self.selection(),baseline)
        self.assertTrue(r['unrelated_unavailable']);self.assertFalse(r['inspection_gaps'])
    def test_frozen_active_part_is_checked_but_cannot_be_edited(self):
        self.spec['members'][0]['maturity']='frozen';selection=self.selection()
        self.assertEqual(selection.components(),[self.part])
        self.assertTrue(hygiene.audit(self.design,self.spec)['automated_checks_passed'])
        with self.assertRaisesRegex(ValueError,'Frozen'):scope.EditBoundary(self.design,selection,self.task(),self.part)
    def test_arbitrary_python_boundary_detects_outside_edits_and_parameters(self):
        b=scope.EditBoundary(self.design,self.selection(),self.task(),self.part)
        self.other.revisionId='r2';self.design.allParameters.values.append(Node(name='unallowed',expression='5 mm'))
        report=b.post();self.assertEqual(len(report['violations']),2)
        self.assertEqual(report['issue_id'],'ISSUE-1');self.assertEqual(report['approval_status'],'not_authenticated')
    def test_narrow_scope_and_parameter_preconditions(self):
        b=scope.EditBoundary(self.design,self.selection(),self.task(),self.part)
        with self.assertRaises(ValueError):b.require_component(self.other)
        with self.assertRaises(ValueError):b.require_parameter('missing')
    def test_reuse_fingerprint_survives_component_rename_not_geometry_or_placement(self):
        sel=self.selection();first=scope.evidence_fingerprint(sel,['carrier'])
        self.part.name='Better Name';self.part.revisionId='rename'
        self.assertEqual(first,scope.evidence_fingerprint(sel,['carrier']))
        self.part.bRepBodies.item(0).revisionId='mounting-hole-moved'
        self.assertNotEqual(first,scope.evidence_fingerprint(sel,['carrier']))
    def test_incomplete_geometry_record_is_unproven(self):
        self.spec['required_checks']=[dict(id='fit',members=['carrier'])]
        self.spec['evidence']=[dict(id='fit',status='pass',source='test',geometry_fingerprint='unknown')]
        self.assertFalse(hygiene.audit(self.design,self.spec)['automated_checks_passed'])
    def test_linked_experiment_rejected_before_regenerate_snapshot_or_build(self):
        ctx=Node(read_only=False,document=Node(allDocumentReferences=Collection([Node()])),synchronize=Mock())
        build=Mock()
        with self.assertRaisesRegex(ValueError,'before mutation'):experiments.try_feature(ctx,'test',build,lambda _:[],{})
        ctx.synchronize.assert_not_called();build.assert_not_called()
    def retirement_context(self):
        self.spec['members'].append(self.member('root',self.root));self.spec['targets']=['root','carrier']
        selection=self.selection();boundary=scope.EditBoundary(self.design,selection,self.task(['root','carrier']),self.root)
        ctx=Node(design=self.design,selection=selection,boundary=boundary,request={'checkpoint_before':True},record=Mock(),check_cancel=Mock(),synchronize=Mock())
        def remove(o):
            self.root.allOccurrences.values.remove(o)
            return Node(name='')
        self.root.features.removeFeatures=Node(add=Mock(side_effect=remove))
        return ctx
    def test_retirement_preserves_shared_active_instance_and_history(self):
        shared=self.occ('carrier:2',self.part);self.root.allOccurrences.values.append(shared)
        ctx=self.retirement_context();r=retirement.retire(ctx,['carrier:1'],'superseded','replacement','Reviewed projections')
        self.assertTrue(r['current_occurrences_verified']);self.assertFalse(r['external_records_updated'])
        self.assertIn(shared,self.root.allOccurrences.values);self.assertTrue(self.part.isValid)
        self.assertEqual(r['removed'][0]['shared_active_instances'],1)
    def test_retired_definition_left_in_history_is_not_active_qa(self):
        ctx=self.retirement_context();retirement.retire(ctx,['carrier:1'],'obsolete','','Reviewed')
        self.part.features.values.append(self.feature('historical-error'))
        self.assertNotIn(self.part,scope.live_components(self.design))
        self.assertFalse(scope.health_snapshot(self.design)[0])
    def test_retirement_dependency_blocker_prevents_remove(self):
        self.o1.joints=Collection([Node()]);ctx=self.retirement_context()
        with self.assertRaisesRegex(ValueError,'joints'):retirement.retire(ctx,['carrier:1'],'obsolete','','Reviewed')
        self.root.features.removeFeatures.add.assert_not_called()
    def test_authoring_circle_drives_dimension_and_checks_constraints(self):
        dimension=Node(parameter=Node(expression=''))
        circle_obj=Node(centerSketchPoint=Node())
        sketch=Node(name='',isFullyConstrained=True,originPoint=Node(),
                    sketchCurves=Node(sketchCircles=Node(addByCenterRadius=Mock(return_value=circle_obj))),
                    geometricConstraints=Node(addCoincident=Mock()),sketchDimensions=Node(addDiameterDimension=Mock(return_value=dimension)))
        self.part.sketches=Node(add=Mock(return_value=sketch));self.part.xYConstructionPlane=Node()
        self.design.userParameters=Node(itemByName=lambda _:Node())
        self.design.unitsManager=Node(isValidExpression=lambda *_:True,evaluateExpression=lambda *_:1.2)
        core.Point3D=Node(create=lambda *x:Node(x=x))
        ctx=Node(target=self.part,design=self.design,check_cancel=Mock(),boundary=None,synchronize=Mock(),created=Mock())
        with patch.object(authoring.advanced,'editable'):
            self.assertIs(authoring.circle(ctx,'sk_bore','insert_diameter'),sketch)
        self.assertEqual(dimension.parameter.expression,'insert_diameter');sketch.geometricConstraints.addCoincident.assert_called_once()
    def dispatcher(self,implementation):
        path=Path(__file__).resolve().parents[1]/'FusionPromptBridge/FusionPromptBridge.py'
        node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
        from FusionPromptBridge import maintainability, reporting
        import uuid
        ns={'design':lambda:self.design,'design_id':lambda:'doc','scopes':scope,'_execute':implementation,'json':json,
            'maintainability':maintainability,'reporting':reporting,'uuid':uuid,'_store':None,'_app':self.app}
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
        return ns['execute']
    def test_narrow_scope_without_task_still_rejects_wrong_target(self):
        action=Mock()
        with self.assertRaisesRegex(ValueError,'outside selected targets'):
            self.dispatcher(action)('rectangle',{'scope':self.spec})
        action.assert_not_called()
    def test_narrow_exception_retains_partial_boundary_and_unknown_validation(self):
        self.spec['members'].append(self.member('root',self.root));self.spec['targets']=['root']
        action=Mock(side_effect=RuntimeError('kernel failed'))
        with self.assertRaisesRegex(RuntimeError,'partial-state report') as caught:
            self.dispatcher(action)('rectangle',{'scope':self.spec,'task':self.task(['root'])})
        self.assertIn('unproven',str(caught.exception));self.assertIn('TASK-1',str(caught.exception))
    def test_added_instance_of_frozen_definition_is_boundary_violation(self):
        self.spec['members'].append(self.member('other',self.other,maturity='frozen'))
        b=scope.EditBoundary(self.design,self.selection(),self.task(),self.part)
        self.root.allOccurrences.values.append(self.occ('other:2',self.other))
        self.assertEqual(b.post()['violations'][0]['kind'],'new_occurrence')
    def test_last_instance_retirement_returns_usable_current_scope(self):
        ctx=self.retirement_context()
        self.spec['required_checks']=[dict(id='old-fit',members=['carrier'])]
        ctx.selection=self.selection()
        r=retirement.retire(ctx,['carrier:1'],'obsolete','','Reviewed')
        refreshed=scope.Selection(self.design,r['current_scope'])
        self.assertEqual(refreshed.target_ids,{'root'})
        self.assertEqual(r['retired_member_ids'],['carrier'])
        self.assertEqual(r['excluded_checks'][0]['id'],'old-fit')
        self.assertNotIn(self.part,ctx.selection.components())
    def test_real_fingerprint_still_needs_complete_revision_members(self):
        self.spec['required_checks']=[dict(id='fit',members=['carrier'])]
        self.spec['evidence']=[dict(id='fit',status='pass',source='test',
            geometry_fingerprint=scope.evidence_fingerprint(self.selection(),['carrier']))]
        self.assertFalse(hygiene.audit(self.design,self.spec)['automated_checks_passed'])
    def test_checked_export_blocks_new_damage_before_file_creation(self):
        ctx=object.__new__(batch_runner.Context);ctx.design=self.design;ctx.target=self.part;ctx.selection=self.selection()
        ctx.check_cancel=Mock();ctx.synchronize=Mock();ctx.record=Mock();ctx.export=Mock()
        ctx.health_baseline=scope.health_snapshot(self.design)
        self.other.features.values.append(self.feature('new-damage'))
        with self.assertRaises(RuntimeError):ctx.export_checked('part.step',manual_review_note='review',scope=self.spec)
        ctx.export.assert_not_called()
    def test_batch_missing_required_evidence_fails_without_claiming_execution_failed(self):
        self.spec['required_checks']=[dict(id='junction',members=['carrier'])]
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp);token=cloud.inspect_state(self.app,self.design,'doc')['edit_token']
            req=dict(operation_id='evidence-test',document_id='doc',component_token='carrier',units='mm',
                     script='def run(ctx): return {}',checkpoint_before=False,validate_after=True,
                     edit_token=token,scope=self.spec)
            job=store.submit(req)
            batch_runner.execute_job(store,store.claim('owner'),self.app,lambda:self.design,lambda:'doc')
            r=store.result(job['job_id'])
            self.assertEqual(r['status'],'failed');self.assertEqual(r['result']['execution_status'],'completed')
            self.assertEqual(r['result']['validation']['evidence_status'],'unproven')
    def test_explicit_empty_scope_is_rejected_not_treated_as_default(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'nonempty'):
                Store(temp).submit(dict(operation_id='empty',document_id='doc',component_token='carrier',units='mm',
                    script='def run(ctx): return {}',checkpoint_before=False,validate_after=True,scope={}))
    def test_retirement_complete_job_refreshes_scope_before_postvalidation(self):
        self.retirement_context()
        task=self.task(['root','carrier'])
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp);token=cloud.inspect_state(self.app,self.design,'doc',writer_id='writer')['edit_token']
            job=store.submit(dict(operation_id='retire-job',document_id='doc',component_token='@root',units='mm',
                script="def run(ctx): return ctx.retire_occurrences(['carrier:1'],'obsolete','','Reviewed')",
                checkpoint_before=True,validate_after=True,edit_token=token,scope=self.spec,task=task))
            with patch.object(batch_runner.Context,'checkpoint',return_value={'fixture':'checkpoint'}):
                batch_runner.execute_job(store,store.claim('owner'),self.app,lambda:self.design,lambda:'doc')
            result=store.result(job['job_id'])
            self.assertEqual(result['status'],'succeeded',result)
            self.assertEqual(result['result']['validation']['scope']['targets'],['root'])
            self.assertEqual(result['result']['return_value']['retired_member_ids'],['carrier'])
    def test_batch_reports_new_damage_even_when_validate_after_false(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp);token=cloud.inspect_state(self.app,self.design,'doc')['edit_token']
            script="def run(ctx):\n    target.features.item(0).healthState=2\n    return {'executed':True}"
            self.part.features=Collection([self.feature('damaged',0)])
            req=dict(operation_id='batch-test',document_id='doc',component_token='carrier',units='mm',script=script,
                     checkpoint_before=False,validate_after=False,edit_token=token,scope=self.spec)
            j=store.submit(req)
            batch_runner.execute_job(store,store.claim('owner'),self.app,lambda:self.design,lambda:'doc')
            r=store.result(j['job_id'])
            self.assertEqual(r['status'],'failed');self.assertEqual(r['result']['execution_status'],'completed')
            self.assertEqual(r['result']['validation']['validation_status'],'fail')

if __name__=='__main__':unittest.main()
