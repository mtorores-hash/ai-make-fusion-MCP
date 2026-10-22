"""Engineering contract 1.0: declared interfaces and bounded checks, not inferred design intent."""
import copy
import json
import time
from pathlib import Path
import adsk.fusion
from . import advanced, design_intent, engineering_geometry as geom, model_tools, scope, verification

VERSION='1.0'
EVALUATOR_REVISION='k1-cad-2026-10-22.1'
CATEGORIES={'continuous_wall':'geometric_quality','gap':'geometric_quality','intersection':'geometric_quality',
            'G1':'geometric_quality','G2':'geometric_quality','access':'assembly_feasibility','solid_probe':'geometric_quality'}
OPERATIONS={'insertion','removal','screwdriver','screw_insertion','connector_engagement','connected_wire','heatset','travel','stop'}


from .job_store import load_engineering_report as load_report


def conclusion(rows):
    if not rows:return 'not_checked'
    if any(r['status']=='fail' for r in rows):return 'fail'
    if any(r['status']!='pass' for r in rows):return 'unproven'
    return 'pass'


class Session:
    def __init__(self,ctx,plan):
        self.ctx=ctx;self.design=ctx.design;self.plan=copy.deepcopy(plan);self.objects={};self.records={}
        if plan.get('version')!=VERSION:raise ValueError('engineering plan.version must be 1.0')
        if plan.get('document_id')!=ctx.request['document_id']:
            raise design_intent.ReferenceFailure('wrong_document','Engineering plan belongs to another document; no token fallback allowed')
        if not ctx.selection or ctx.selection.legacy:raise ValueError('Engineering checks need explicit current selected scope')
        self.selection=scope.Selection(ctx.design,ctx.selection.current_spec())
        self.interfaces=plan.get('interfaces',{})
        if not isinstance(self.interfaces,dict) or not self.interfaces:raise ValueError('Nonempty interfaces map required')
        self.parameters={p.name:p.expression for p in model_tools.each(ctx.design.allParameters)}
        self.diagnostics={'resolved_interfaces':0,'kernel_intersections':0,'distance_calls':0,'reused_checks':0}
    def resolve(self,ident):
        if ident in self.objects:return self.objects[ident]
        record=self.interfaces[ident];reference=record['reference']
        if bool(reference.get('tag'))==bool(reference.get('token')):raise ValueError('Reference needs exactly one token or semantic tag')
        method='entity_token'
        if reference.get('tag'):
            resolved=design_intent.resolve_tag(self.design,reference['tag'],diagnostics=True)
            reference=dict(token=resolved['entity']['token'],occurrence_token=reference.get('occurrence_token',''))
            method=resolved['method']
        entity=model_tools.resolve_ref(self.design,reference,True)
        body=advanced.native(geom.body_of(entity))
        if not self.selection.contains(body.parentComponent):raise ValueError('Engineering interface outside selected targets/dependencies')
        if not body.isValid:raise design_intent.ReferenceFailure('reference_stale','Interface body invalid')
        revision=body.revisionId;occurrence=getattr(entity,'assemblyContext',None)
        metadata={'entity':model_tools.ref(entity),'body':model_tools.ref(body),'body_revision':revision,
                  'component_revision':body.parentComponent.revisionId,'resolution_method':method,
                  'placement_cm':occurrence.transform2.asArray() if occurrence else None,'parameters':{},'evidence_gaps':[]}
        for name in record.get('parameter_names',[]):
            if name not in self.parameters:raise ValueError('Unresolved parameter dependency: '+name)
            metadata['parameters'][name]=self.parameters[name]
        names=set()
        for dim in record.get('dimensions',[]):
            for k in ('nominal_mm','lower_deviation_mm','upper_deviation_mm'):verification.finite(dim[k],k)
            if not dim.get('name') or dim['name'] in names or dim['lower_deviation_mm']>0 or dim['upper_deviation_mm']<0:
                raise ValueError('Named dimension uncertainty must bracket zero')
            names.add(dim['name'])
            if dim.get('provenance') not in ('measured','manufacturer','assumed') or not dim.get('source'):
                raise ValueError('Dimension needs measured/manufacturer/assumed provenance and source')
            if dim.get('geometry_revision')!=revision:metadata['evidence_gaps'].append('stale dimension evidence: '+dim['name'])
            if dim['provenance']=='assumed':metadata['evidence_gaps'].append('assumed dimension: '+dim['name'])
        if record.get('mating_direction') is not None:geom.unit(record['mating_direction'])
        # Datums are named references to other declared interfaces, not untraceable points.
        for datum in record.get('datums',[]):
            if datum not in self.interfaces:raise ValueError('Unresolved datum interface: '+datum)
        self.objects[ident]=entity;self.records[ident]=metadata;self.diagnostics['resolved_interfaces']+=1
        return entity
    def dependencies(self,ids):
        result=set(ids);pending=list(ids)
        while pending:
            ident=pending.pop();self.resolve(ident)
            for datum in self.interfaces[ident].get('datums',[]):
                if datum not in result:result.add(datum);pending.append(datum)
        return sorted(result)
    def state(self,ids):
        ids=self.dependencies(ids)
        return {i:{'definition':self.interfaces[i], 'body':self.records[i]['body'],'resolved_entity':self.records[i]['entity'],
                   'revision':self.records[i]['body_revision'],'placement_cm':self.records[i]['placement_cm'],
                   'parameters':self.records[i]['parameters']} for i in ids}
    def protected(self):
        result={}
        for ident,definition in self.interfaces.items():
            if definition.get('protected'):
                try:
                    entity=self.resolve(ident)
                    result[ident]={'signature':geom.signature(entity),'placement_cm':self.records[ident]['placement_cm'],
                                   'reference':definition['reference'],'tolerances':definition.get('protected_tolerances',{}),
                                   'body_revision':self.records[ident]['body_revision']}
                except Exception as exc:
                    result[ident]={'status':'unproven','blocker':str(exc)}
        return result
    def check(self,item):
        kind=item['kind'];tol=item.get('limits',{})
        if kind=='access':return self.access(item)
        ids=item['interfaces']
        if kind=='solid_probe':
            from .cad_review import probe_bounds
            if len(ids)!=1:raise ValueError('Solid probe requires exactly one body interface')
            body=self.resolve(ids[0])
            if not adsk.fusion.BRepBody.cast(body) or not body.isSolid:raise ValueError('Solid probe requires a solid body')
            volume,minimum=probe_bounds(item)
            if item['probe'].get('geometry_revision')!=self.records[ids[0]]['body_revision']:
                raise ValueError('Probe declaration is stale for the body revision')
            self.ctx.check_cancel()
            probe=geom.envelope_box(item['probe'],[0,0,0])
            with self.ctx.operation('solid_probe_intersection',target=self.records[ids[0]]['body']):
                result=geom.overlap(probe,geom.temporary_world(body))
            self.diagnostics['kernel_intersections']+=result['method']=='temporary_BRep_intersection'
            fraction=result['volume_mm3']/volume
            return dict(result,status='pass' if fraction>=minimum else 'fail',fill_fraction=fraction,
                        probe=item['probe'],probe_volume_mm3=volume,
                        claim='Occupancy of the declared finite box only',
                        not_checked=['connectivity_to_adjacent_regions','global_minimum_wall_thickness',
                                     'undeclared_junctions','strength','slicer_supports'])
        if len(ids)!=2:raise ValueError('Geometric checks require exactly two interface IDs')
        a,b=(self.resolve(i) for i in ids)
        if kind=='continuous_wall':
            self.diagnostics['distance_calls']+=1
            report=geom.planar_wall(self.ctx.app,a,b,tol)
            return dict(report,status='fail' if report['failed_metrics'] else 'pass',
                        not_checked=['minimum_wall_thickness','junction_attachment_extent','aesthetic_quality'])
        if kind=='gap':
            self.diagnostics['distance_calls']+=1
            result=geom.distance(self.ctx.app,a,b)
            low=verification.finite(tol['min_mm'],'minimum gap',True);high=verification.finite(tol['max_mm'],'maximum gap',True)
            if low>high:raise ValueError('Reversed gap interval')
            return dict(result,status='pass' if low<=result['gap_mm']<=high else 'fail',
                        not_checked=['penetration_volume','minimum_wall_thickness'])
        if kind=='intersection':
            if not adsk.fusion.BRepBody.cast(a) or not adsk.fusion.BRepBody.cast(b):raise ValueError('Intersection check requires body interfaces')
            if not a.isSolid or not b.isSolid:raise ValueError('Intersection requires solid bodies')
            self.diagnostics['kernel_intersections']+=1
            result=geom.overlap(geom.temporary_world(a),geom.temporary_world(b))
            limit=verification.finite(tol['max_volume_mm3'],'allowed overlap',True)
            if limit>0 and not item.get('intent_reason'):raise ValueError('Allowed interference requires explicit intent_reason')
            return dict(result,status='pass' if result['volume_mm3']<=limit else 'fail',not_checked=['self_intersections_within_one_body'])
        if kind in ('G1','G2'):
            result=geom.join_samples(a,b,tol,item.get('samples',5),kind=='G2')
            # Even G1 agreement is only sampled; caller acceptance method decides readiness.
            return dict(result,status='fail' if result['failed_samples'] else 'unproven',
                        observed='sampled_discontinuity' if result['failed_samples'] else 'sampled_agreement')
        raise ValueError('Unsupported geometric check kind: '+str(kind))
    def access(self,item):
        moving=item['moving'];self.resolve(moving)
        if item.get('operation') not in OPERATIONS:raise ValueError('Declare an assembly/service operation')
        box=self.interfaces[moving]['envelopes'][item['envelope']]
        if box.get('frame')!='world_mm':raise ValueError('Envelope frame must be explicit world_mm')
        if not box.get('source') or box.get('geometry_revision')!=self.records[moving]['body_revision']:
            raise ValueError('Envelope needs source and current body geometry_revision')
        positions=item['translations_mm'];budget=item['max_samples']
        if type(budget) is not int or not 1<=len(positions)<=budget<=4096:raise ValueError('Require 1..max_samples<=4096 explicit translations')
        obstacles=item['obstacles']
        if not obstacles:raise ValueError('Explicit nonempty obstacle set required')
        solids={}
        for ident in obstacles:
            entity=self.resolve(ident)
            if not adsk.fusion.BRepBody.cast(entity) or not entity.isSolid:raise ValueError('Access obstacles must be solid body interfaces')
            solids[ident]=geom.temporary_world(entity)
        rows=[];limit=verification.finite(item['limits']['max_volume_mm3'],'allowed contact volume',True)
        if limit>0 and not item.get('intent_reason'):raise ValueError('Allowed path contact requires an intent_reason')
        for i,position in enumerate(positions):
            self.ctx.check_cancel();probe=geom.envelope_box(box,position)
            for ident,body in solids.items():
                result=geom.overlap(probe,body);self.diagnostics['kernel_intersections']+=result['method']=='temporary_BRep_intersection'
                rows.append(dict(result,pose=i,translation_mm=position,obstacle=ident,entity=self.records[ident]['entity'],blocked=result['volume_mm3']>limit))
        blocked=[r for r in rows if r['blocked']]
        return {'status':'fail' if blocked else 'pass' if len(positions)==1 else 'unproven',
                'observed':'envelope_obstructed' if blocked else 'clear_at_declared_poses','poses':len(positions),
                'envelope':box,'samples':rows,'blocked_samples':len(blocked),'continuous_collision_proof':False,
                'not_checked':['obstacles_outside_declared_set','envelope_representation_accuracy']+(['between_poses'] if len(positions)>1 else []),
                'limitation':'Conservative box collision rejects the declared envelope; actual detailed-part access may still be possible. No occurrence was moved.'}


def compare_protected(before,after):
    rows=[]
    for ident in before.keys()|after.keys():
        if ident not in before or ident not in after or 'signature' not in before[ident] or 'signature' not in after[ident]:
            rows.append({'id':ident,'status':'unproven','reason':'missing protected interface'});continue
        fields=geom.signature_changes(before[ident]['signature'],after[ident]['signature'],before[ident]['tolerances'])
        if before[ident]['placement_cm']!=after[ident]['placement_cm']:fields.append('placement')
        rows.append({'id':ident,'status':'fail' if fields else 'pass','changed_metrics':fields,
                     'claim':'Declared signature metrics and placement only; not complete shape equivalence'})
    return {'status':conclusion(rows),'interfaces':rows}


def verify(ctx,plan,previous_job_id='',detail=False):
    started=time.perf_counter();ctx.check_cancel();session=Session(ctx,plan)
    checks=plan.get('checks',[])
    if not checks or len(checks)>256:raise ValueError('Provide 1..256 explicitly scoped checks')
    if any(not c.get('id') for c in checks) or len({c['id'] for c in checks})!=len(checks):raise ValueError('Unique check IDs required')
    previous=load_report(ctx.store,previous_job_id) if previous_job_id else None
    if previous and previous['document_id']!=plan['document_id']:raise ValueError('Evidence reuse requires same document identity')
    cached={c['id']:c for c in previous['checks']} if previous else {}
    rows=[]
    for item in checks:
        ctx.check_cancel();begin=time.perf_counter();ident=item['id'];kind=item['kind']
        row={'id':ident,'kind':kind,'category':CATEGORIES.get(kind,'geometric_quality'),'status':'unproven','intent':item.get('intent_reason','declared requirement')}
        try:
            ids=[item['moving']]+item['obstacles'] if kind=='access' else item['interfaces']
            deps=session.state(ids);digest=verification.fingerprint({'version':VERSION,'evaluator_revision':EVALUATOR_REVISION,'check':item,'dependencies':deps})
            if item.get('contradicted_by'):
                raise ValueError('Unresolved contradictory evidence: '+str(item['contradicted_by']))
            old=cached.get(ident)
            if old and old.get('dependency_fingerprint')==digest:
                row=copy.deepcopy(old);row['reused_from_job']=previous_job_id;session.diagnostics['reused_checks']+=1
            else:
                row['dependencies']=deps;row['entities']={i:session.records[i]['entity'] for i in deps}
                row['limits']=item.get('limits',{})
                row.update(session.check(item));row['dependency_fingerprint']=digest;row['dependencies']=deps
                row['entities']={i:session.records[i]['entity'] for i in deps}
                row['limits']=item.get('limits',{})
            gaps=[g for i in deps for g in session.records[i]['evidence_gaps']]
            if gaps:
                row['evidence_gaps']=gaps
                if row['status']=='pass':row['status']='unproven'
        except Exception as exc:
            if getattr(exc,'code',None) in ('cancelled','wrong_document'):raise
            # A failed evaluator is unavailable evidence, not successful geometry.
            row.update(status='unproven',error_code=getattr(exc,'code','check_unavailable'),blocker=str(exc),
                       next_action='Inspect this reference/requirement and change the recovery method; do not repeat an unchanged failed call.')
        row['evaluation_provenance']={'representation':'Fusion_native_BRep','evaluator_revision':EVALUATOR_REVISION,
                                      'method':row.get('method',kind),'document_id':plan['document_id']}
        row['duration_seconds']=time.perf_counter()-begin;rows.append(row)
    ctx.check_cancel()
    health=scope.health_report(ctx.design,session.selection,getattr(ctx,'health_baseline',None))
    protected=session.protected()
    protected_gaps=[name for name,value in protected.items() if 'signature' not in value]
    report={'schema':VERSION,'document_id':plan['document_id'],'checks':rows,'interfaces':session.records,'protected':protected,
            'conclusions':{'native_health':health['validation_status'],
                           'geometric_quality':conclusion([r for r in rows if r['category']=='geometric_quality']),
                           'assembly_feasibility':conclusion([r for r in rows if r['category']=='assembly_feasibility']),
                           'manufacturing_readiness':'not_checked'},
            'native_health':health,'approval_status':'not_evaluated','scope':session.selection.report(),
            'diagnostics':session.diagnostics,'duration_seconds':time.perf_counter()-started,
            'not_checked':['undeclared_interfaces','global_minimum_wall_thickness','junction_attachment_extent',
                           'aesthetic_acceptance','slicer_supports','physical_assembly']}
    report['protected_reference_gaps']=protected_gaps
    if previous and (previous.get('protected') or protected):
        report['protected_comparison']=compare_protected(previous.get('protected',{}),protected)
    if session.selection.gaps:
        report['dependency_scope_gaps']=session.selection.gaps
        for category,value in report['conclusions'].items():
            if value=='pass':report['conclusions'][category]='unproven'
    summary={'schema':VERSION,'conclusions':report['conclusions'],'checks':[
        {k:r[k] for k in ('id','status','kind','duration_seconds','blocker','error_code','reused_from_job','evidence_gaps') if k in r} for r in rows],
        'failed':[r['id'] for r in rows if r['status']=='fail'],'unproven':[r['id'] for r in rows if r['status']=='unproven'],
        'duration_seconds':report['duration_seconds'],'diagnostics':session.diagnostics,'not_checked':report['not_checked'],
        'approval_status':'not_evaluated','detail_request':{'job_id':ctx.job_id,'section':'engineering'}}
    summary['protected_reference_gaps']=protected_gaps
    if 'protected_comparison' in report:summary['protected_comparison']=report['protected_comparison']
    if session.selection.gaps:summary['dependency_scope_gaps']=session.selection.gaps
    for compact,row in zip(summary['checks'],rows):
        if row['status']=='fail':
            compact['evidence']={k:row[k] for k in ('entities','limits','gap_mm','step_mm','normal_angle_deg',
                                                  'volume_mm3','location_mm','points_mm','section_hint') if k in row}
            if row.get('samples'):
                compact['evidence']['first_failure']=next((s for s in row['samples'] if s.get('blocked') or s.get('failed')),None)
    # Preserve detail on disk rather than repeating topology/sample arrays in every job response.
    name='engineering_%03d.json'%sum(1 for f in ctx.result['files'] if Path(f['path']).name.startswith('engineering_'))
    path=ctx.path(name);path.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    artifact=ctx.artifact(path);ctx.result['engineering_report']={'summary':summary,'artifact':artifact};ctx.flush()
    return report if detail else summary
