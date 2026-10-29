"""Trusted full-API script execution. Entry points MUST be called on Fusion's main thread."""
import contextlib
import hashlib
import io
import json
import math
from pathlib import Path
import re
import time
import traceback
import adsk.core
import adsk.fusion
from . import advanced, model_tools, verification, cloud, maintainability
from . import scope as scopes
from .execution_policy import validate_read_only, validate_reconciliation
from .design_intent import ReferenceFailure
import ast

class Cancelled(Exception):
    code='cancelled'

class LimitedLog(io.TextIOBase):
    def __init__(self,limit=1_000_000): self.parts=[]; self.size=0; self.limit=limit; self.truncated=False
    def write(self,text):
        space=max(self.limit-self.size,0); self.parts.append(text[:space]); self.size+=min(len(text),space)
        self.truncated |= len(text)>space
        return len(text)
    def getvalue(self): return ''.join(self.parts)+ ('\n[log truncated]' if self.truncated else '')

def inventory(d, components=None):
    entities=[]
    for c in (components if components is not None else model_tools.each(d.allComponents)):
        entities.append(c)
        for collection in (c.bRepBodies,c.sketches,c.features,c.joints,c.asBuiltJoints):
            entities.extend(model_tools.each(collection))
    return entities

class Context:
    def __init__(self,store,job,app,design,target,guard):
        self.store=store; self.job_id=job['job_id']; self.operation_id=job['operation_id']
        self.request=job['request']; self.app=app; self.design=design; self.target=target
        self.document=app.activeDocument; self.units=self.request['units']; self.guard=guard
        self.selection=None;self.boundary=None;self.health_baseline=None;self.authoring=None;self.started=time.monotonic()
        self.reconciliation=self.request.get('mode')=='reconcile'
        self.read_only=self.request.get('mode','modeling') in ('read_only','reconcile')
        self.timings={k:0.0 for k in ('solve','measurement','export','checkpoint','script')}
        self.output_dir=store.root/'artifacts'/self.job_id
        self.output_dir.mkdir(parents=True,exist_ok=True)
        self.result={'created':[],'measurements':{},'warnings':[],'files':[],'checkpoints':[],
                     'traceback':None,'return_value':None,'validation':None,'timings_seconds':self.timings,
                     'outcomes':{'execution':'not_started','export':'not_requested','presentation':'not_requested',
                                 'engineering':'not_checked','readiness':'not_evaluated','approval':'not_evaluated'}}

    @contextlib.contextmanager
    def operation(self, name, target=None, tools=None):
        """Persist before entering a blocking native call. No heartbeat implies progress."""
        import uuid
        ident=uuid.uuid4().hex;started=time.perf_counter()
        data={'operation':str(name),'activity_id':ident,'target':target,'tools':tools,
              'last_completed_stage':self.result.get('last_completed_stage'),
              'checkpoint':(self.result.get('checkpoints') or [None])[-1]}
        self.flush();self.store.event(self.job_id,'operation_started',data)
        outcome='failed'
        try:
            yield
            outcome='completed'
        finally:
            self.store.event(self.job_id,'operation_finished',dict(data,status=outcome,elapsed_seconds=time.perf_counter()-started))

    def native_call(self,name,action,target=None,tools=None):
        self.check_cancel()
        with self.operation(name,target,tools):return action()

    @contextlib.contextmanager
    def timed(self, category):
        start=time.perf_counter()
        try:
            with self.operation(category):yield
        finally: self.timings[category]+=time.perf_counter()-start

    def _synchronized_revision_state(self):
        # Optimistic revision guard only, not geometry equivalence or evidence refresh.
        return (scopes.revisions(self.design),
                [(p.name,p.expression) for p in model_tools.each(self.design.allParameters)])

    def synchronize(self, predicate=None, max_events=20, timeout_seconds=2.0, recompute=True):
        if type(max_events) is not int or not 1<=max_events<=1000:
            raise ValueError('max_events must be 1..1000')
        if not 0<verification.finite(timeout_seconds)<=30:
            raise ValueError('timeout_seconds must be >0 and <=30')
        self.check_cancel()
        if self.read_only and recompute: raise ValueError('Read-only queries cannot regenerate')
        start=time.perf_counter()
        with self.timed('solve'):
            if recompute and not self.design.computeAll(): raise RuntimeError('Fusion computeAll failed')
            for _ in range(max_events):
                self.check_cancel()
                if predicate is None or predicate():
                    if recompute:self._last_synchronized_revision_state=self._synchronized_revision_state()
                    return True
                if time.perf_counter()-start>=timeout_seconds: break
                adsk.doEvents()
        raise RuntimeError('Solver synchronization exhausted its event/time bound; pose unverified')

    def check_cancel(self):
        self.guard()
        if self.authoring and self.authoring.remaining_seconds() is not None and self.authoring.remaining_seconds()<=0:
            raise Cancelled('Adopted cumulative issue time exhausted at cooperative boundary; native calls cannot be interrupted')
        bound=self.request.get('task',{}).get('max_seconds')
        if bound is not None and time.monotonic()-self.started>bound:
            raise Cancelled('Caller per-operation time bound reached at cooperative checkpoint; kernel calls cannot be interrupted')
        if self.store.row(self.job_id)['cancel_requested']: raise Cancelled('Cancellation requested at cooperative boundary.')

    def flush(self): self.store.partial(self.job_id,self.result)
    def progress(self,fraction,message):
        self.check_cancel(); self.store.progress(self.job_id,fraction,message)
        self.store.event(self.job_id,'progress',{'operation':str(message)[:512],'fraction':fraction,
            'last_completed_stage':self.result.get('last_completed_stage')});self.flush()
    def warn(self,message): self.result['warnings'].append(str(message)); self.flush()
    def record(self,name,value):
        json.dumps(value,allow_nan=False); self.result['measurements'][name]=value; self.flush(); return value
    def created(self,entity):
        value=model_tools.ref(entity); self.result['created'].append(value); return entity
    def ref(self,entity): return model_tools.ref(entity)
    def resolve(self,reference,world=False): return model_tools.resolve_ref(self.design,reference,world)
    def value(self,expression):
        # Strings must carry units or reference named parameters; floats use declared request units.
        if isinstance(expression,(int,float)): expression=str(expression)+' '+self.units
        return adsk.core.ValueInput.createByString(expression)
    def point(self,x,y,z=0):
        factor={'mm':0.1,'cm':1,'m':100,'in':2.54}[self.units]
        return adsk.core.Point3D.create(x*factor,y*factor,z*factor)
    def parameter(self,name,expression,unit=None):
        if self.boundary:self.boundary.require_parameter(name)
        p=self.design.userParameters.itemByName(name)
        if p: p.expression=expression
        else: p=self.design.userParameters.add(name,adsk.core.ValueInput.createByString(expression),unit or self.units,'Batch MCP')
        return p
    def audit_hygiene(self, scope=None):
        from .hygiene import audit
        self.check_cancel()
        return audit(self.design,scope if scope is not None else (self.selection.current_spec() if self.selection and not self.selection.legacy else None),
                     [m['id'] for m,c in self.selection.entries if c.revisionId!=m['revision']] if self.selection and not self.selection.legacy else [])
    def require_hygiene(self,strict_reviews=False,scope=None):
        from .hygiene import require
        report=self.audit_hygiene(scope)
        self.record('modeling_hygiene',report)
        return require(report,strict_reviews)
    def export_checked(self,filename,entity=None,manual_review_note='',strict_reviews=False,scope=None,engineering_plan=None,previous_job_id=''):
        if not isinstance(manual_review_note,str) or not manual_review_note.strip():
            raise ValueError('Record a manual_review_note covering non-automated rules before a checked export')
        self.check_cancel()
        entity=entity or self.target
        chosen=scope if scope is not None else (self.selection.current_spec() if self.selection and not self.selection.legacy else scopes.selected(self.design,advanced.native(entity) if adsk.fusion.Component.cast(advanced.native(entity)) else advanced.native(entity).parentComponent))
        selection=scopes.Selection(self.design,chosen);selection.check_export(entity)
        if getattr(self,'_last_synchronized_revision_state',None)==self._synchronized_revision_state():
            self.synchronize(recompute=False)
        else:self.synchronize()
        # Recompute must not silently make a supplied revision scope current.
        selection=scopes.Selection(self.design,chosen);selection.check_export(entity)
        integrity=scopes.health_report(self.design,selection,getattr(self,'health_baseline',None))
        self.record('checked_export_integrity',integrity)
        if integrity['feature_errors'] or integrity['inspection_gaps']:
            raise RuntimeError('Checked export blocked by new/relevant integrity errors or unavailable checks')
        boundary=getattr(self,'boundary',None)
        if boundary and boundary.post().get('violations'):raise RuntimeError('Checked export blocked by edit-scope violation')
        report=self.require_hygiene(strict_reviews,chosen)
        self.record('modeling_hygiene_manual_review',manual_review_note)
        engineering=None
        if engineering_plan is not None:
            engineering=self.verify_engineering(engineering_plan,previous_job_id)
            if any(row['status']!='pass' for row in engineering['checks']) or engineering.get('dependency_scope_gaps') or engineering.get('protected_reference_gaps'):
                raise RuntimeError('Checked export blocked by failed/unproven engineering checks; see engineering report')
            if engineering.get('protected_comparison',{}).get('status','pass')!='pass':
                raise RuntimeError('Checked export blocked by protected geometry comparison')
        artifact=self.export(filename,entity,capture_identity=True) if engineering_plan is not None else self.export(filename,entity)
        result={'artifact':artifact,'hygiene':report,'manual_review_note':manual_review_note,
                'scope':selection.report(),'validation_status':'pass','approval_status':'not_evaluated',
                'integrity':integrity,
                'claim':'Selected automated checks and caller-reported evidence; not whole-assembly approval.'}
        if engineering is not None:result['engineering']=engineering
        self.record('checked_export_'+filename,result)
        return result
    def tag_geometry(self,body,name,kind,filters,feature=None,role='functional',requirement='',signature_tolerances=None,allow_feature_fallback=False):
        from .design_intent import tag_geometry
        return tag_geometry(self.design,body,name,kind,filters,feature,role,requirement,signature_tolerances,allow_feature_fallback)
    def resolve_tag(self,name,diagnostics=False):
        from .design_intent import resolve_tag
        return resolve_tag(self.design,name,diagnostics)
    def surface_audit(self,body,short_edge_mm,small_face_mm2,slender_width_mm,protected_entities=(),intent_plan=None):
        from .design_intent import surface_audit
        with self.timed('measurement'):
            result=surface_audit(body,short_edge_mm,small_face_mm2,slender_width_mm,protected_entities)
            if intent_plan is not None:result['intent_checks']=self.verify_engineering(intent_plan)
            return result
    def verify_engineering(self,plan,previous_job_id='',detail=False):
        from .engineering import verify
        value=verify(self,plan,previous_job_id,detail)
        self.result['outcomes']['engineering']='evaluated_see_conclusions';self.flush();return value
    def reconcile_edit(self,job_id):
        from .recovery import reconcile
        return reconcile(self,job_id)

    def reconcile_authoring(self,issue_id,original_job_id=''):
        from .authoring_recovery import inspect
        return inspect(self,issue_id,original_job_id)

    def acknowledge_authoring(self,issue_id,observation_id,note,original_job_id=''):
        from .authoring_recovery import acknowledge
        return acknowledge(self,issue_id,observation_id,note,original_job_id)
    def run_stage(self,stage_id,action,postcondition,protected_plan=None):
        from .recovery import run_stage
        return run_stage(self,stage_id,action,postcondition,protected_plan)
    def retire_occurrences(self,occurrence_tokens,reason,replacement_id='',dependency_review_note=''):
        from .retirement import retire
        return retire(self,occurrence_tokens,reason,replacement_id,dependency_review_note)
    def parametric_circle(self,name,diameter_parameter):
        from .authoring import circle
        return circle(self,name,diameter_parameter)
    def try_feature(self,*args,**kwargs):
        from .experiments import try_feature
        return try_feature(self,*args,**kwargs)
    def geometry_snapshot(self,bodies,protected=None):
        from .experiments import snapshot
        return snapshot(self.design,bodies,protected)
    def release_manifest(self,model_revision,entries,checks,filename='release_manifest.json',manufacturing=None):
        manifest=verification.build_manifest(model_revision,entries,checks)
        if manufacturing is not None:
            from .manufacturing import handoff
            manifest['manufacturing']=handoff(self,manifest['artifacts'],manufacturing)
        path=self.path(filename)
        path.write_text(json.dumps(manifest,indent=2,allow_nan=False),encoding='utf-8')
        return dict(manifest=manifest,file=self.artifact(path))
    def select_edges(self,body,filters=None,feature=None): return model_tools.select(body,'edge',filters,feature)
    def select_faces(self,body,filters=None,feature=None): return model_tools.select(body,'face',filters,feature)
    @staticmethod
    def expect_one(matches):
        if len(matches)!=1: raise ValueError('Expected exactly one geometry match; got '+str(len(matches)))
        return matches[0]
    def inspect(self,include_topology=False,scope=None): return model_tools.inspect_full(self.design,include_topology,scope=scope if scope is not None else (self.selection.current_spec() if self.selection and not self.selection.legacy else None))
    def evidence_fingerprint(self,member_ids):
        if not self.selection or self.selection.legacy:raise ValueError('Explicit scope required for evidence reuse')
        return scopes.evidence_fingerprint(self.selection,member_ids)
    def validate(self,scope=None): return model_tools.validate(self.design,scope if scope is not None else (self.selection.current_spec() if self.selection and not self.selection.legacy else None))
    def minimum_distance(self,one,two):
        with self.timed('measurement'): return model_tools.measure(self.app,self.design,one,two)
    def interference(self,references):
        with self.timed('measurement'): return model_tools.interference(self.design,references)
    def clearance_budget(self,*args,**kwargs): return verification.clearance_budget(*args,**kwargs)
    def artifact(self,path):
        path=Path(path).resolve()
        if not path.is_file(): raise ValueError('Artifact does not exist: '+str(path))
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''): digest.update(block)
        entry={'path':str(path),'bytes':path.stat().st_size,'sha256':digest.hexdigest()}
        self.result['files']=[e for e in self.result['files'] if e['path']!=str(path)]+[entry]
        self.flush(); return entry
    def path(self,filename):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,160}',filename): raise ValueError('Use a simple filename.')
        path=self.output_dir/filename
        if path.exists(): raise ValueError('Output already exists; use a unique filename.')
        return path
    def export(self,filename,entity=None,capture_identity=False):
        self.check_cancel(); path=self.path(filename); manager=self.design.exportManager
        suffix=path.suffix.lower(); entity=entity or self.target
        from .manufacturing import identity
        source=identity(self,entity) if capture_identity else None
        if suffix=='.f3d': opts=manager.createFusionArchiveExportOptions(str(path),entity)
        elif suffix in ('.step','.stp'): opts=manager.createSTEPExportOptions(str(path),entity)
        elif suffix=='.stl':
            opts=manager.createSTLExportOptions(entity,str(path)); opts.sendToPrintUtility=False
        else: raise ValueError('Supported exports: f3d, step, stp, stl.')
        try:
            with self.timed('export'):
                if not manager.execute(opts) or not path.exists():raise RuntimeError('Fusion export failed: '+filename)
        except Exception:
            self.result['outcomes']['export']='partial_failure' if self.result['outcomes']['export']=='completed' else 'failed'
            self.flush();raise
        artifact=self.artifact(path)
        if source is not None:
            if identity(self,entity)!=source:
                self.result['outcomes']['export']='identity_unproven';self.flush()
                raise RuntimeError('Geometry changed during export; artifact is not revision-matched')
            artifact['geometry_identity']=source
            self.flush()
        if self.result['outcomes']['export'] in ('not_requested','completed'):self.result['outcomes']['export']='completed'
        self.flush()
        return artifact
    def checkpoint(self,label):
        self.check_cancel()
        if self.document.allDocumentReferences.count:
            record=cloud.cloud_checkpoint(self.app,self.design,self.request['document_id'])
            path=self.path('checkpoint_%03d_cloud.json'%len(self.result['checkpoints']))
            path.write_text(json.dumps(record,indent=2),encoding='utf-8')
            artifact=dict(self.artifact(path),kind='cloud_version',recovery=record)
            self.result['checkpoints'].append(dict(artifact,label=label)); self.flush(); return artifact
        clean=re.sub(r'[^A-Za-z0-9_-]+','_',label)[:70] or 'checkpoint'
        filename='checkpoint_%03d_%s.f3d'%(len(self.result['checkpoints']),clean)
        with self.timed('checkpoint'):
            artifact=self.export(filename,self.design.rootComponent)
        self.result['checkpoints'].append(dict(artifact,label=label)); self.flush(); return artifact
    def stage(self,label,fraction,checkpoint=True):
        self.progress(fraction,label)
        if checkpoint: self.checkpoint(label)
    def section_sketch(self,body,plane='XY',offset='0 mm',name='MCP Section'):
        """Create editable section curves in body's native component (not a clipping analysis)."""
        self.check_cancel(); body=advanced.native(body); c=body.parentComponent
        advanced.editable(self.design,c)
        planes={'XY':c.xYConstructionPlane,'XZ':c.xZConstructionPlane,'YZ':c.yZConstructionPlane}
        base=planes[plane]; inp=c.constructionPlanes.createInput()
        if not inp.setByOffset(base,self.value(offset)): raise RuntimeError('Section plane definition failed.')
        cutting_plane=self.created(c.constructionPlanes.add(inp)); cutting_plane.name=name+' Plane'
        sketch=self.created(c.sketches.add(cutting_plane)); sketch.name=name
        curves=sketch.projectCutEdges(body)
        return {'sketch':self.ref(sketch),'plane':self.ref(cutting_plane),'curve_count':curves.count,
                'note':'Section curves are component-local. This does not hide or clip solid geometry.'}
    def export_print_copy(self,body,transform,stem='print_part'):
        """Apply a Matrix3D to a temporary copy, export STL/STEP, remove the copy.
        Transform is component-local to desired print frame, native cm. Source stays unchanged.
        """
        self.check_cancel(); body=advanced.native(body)
        occ=self.design.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        try:
            copied=body.copyToComponent(occ)
            if not copied: raise RuntimeError('Body copy failed.')
            copied=advanced.native(copied)
            if copied.parentComponent != occ.component:
                copied.deleteMe()
                raise RuntimeError('Copy landed in an unexpected component; export stopped.')
            collection=adsk.core.ObjectCollection.create(); collection.add(copied)
            moves=occ.component.features.moveFeatures; inp=moves.createInput2(collection)
            if not inp.defineAsFreeMove(transform): raise RuntimeError('Print transform rejected.')
            moves.add(inp)
            return {'stl':self.export(stem+'.stl',copied),'step':self.export(stem+'.step',occ.component)}
        finally:
            if not occ.deleteMe(): self.warn('Temporary print-export component could not be removed; inspect model.')
    def import_step(self,path):
        self.check_cancel(); path=Path(path)
        if not path.is_absolute() or not path.is_file() or path.suffix.lower() not in ('.step','.stp'):
            raise ValueError('Provide an existing absolute STEP path.')
        manager=self.app.importManager
        opts=manager.createSTEPImportOptions(str(path))
        if not manager.importToTarget(opts,self.target): raise RuntimeError('STEP import failed.')
        return self.inspect(False)
    def capture(self,filename='view.png',width=1920,height=1080,required=True):
        self.check_cancel()
        if not 1<=width<=8192 or not 1<=height<=8192: raise ValueError('Invalid image dimensions.')
        path=self.path(filename)
        if path.suffix.lower()!='.png': raise ValueError('Use a PNG filename.')
        try:
            with self.operation('capture',{'filename':filename,'width':width,'height':height}):
                if not self.app.activeViewport.saveAsImageFile(str(path),width,height):raise RuntimeError('Capture failed.')
                from .png_check import dimensions
                size=dimensions(path)
                if size!=(width,height):raise RuntimeError('Fusion returned unexpected image dimensions: '+str(size))
                artifact=self.artifact(path)
            self.result['outcomes']['presentation']='partial_failure' if self.result.get('presentation_failures') else 'completed'
            self.flush();return artifact
        except Exception as exc:
            self.result['outcomes']['presentation']='failed'
            failure={'status':'failed','filename':filename,'message':str(exc),'required':required,'regeneration_performed':False}
            self.result.setdefault('presentation_failures',[]).append(failure);self.flush()
            if required:raise
            return failure
    def camera(self,eye,target,up=(0,0,1),fit=False):
        self.check_cancel(); viewport=self.app.activeViewport; camera=viewport.camera
        camera.eye=self.point(*eye); camera.target=self.point(*target)
        camera.upVector=adsk.core.Vector3D.create(*up); camera.isFitView=fit
        camera.isSmoothTransition=False; viewport.camera=camera; viewport.refresh()
    def present(self,filename='view.png',eye=None,target=None,up=(0,0,1),width=1920,height=1080):
        """Bounded capture with optional temporary camera, no computeAll or appearances."""
        from .recovery import observe,changes
        self.check_cancel();before=observe(self);viewport=self.app.activeViewport;original=viewport.camera
        if (eye is None)!=(target is None):raise ValueError('Supply both eye and target, or neither')
        result={};restore_error=None
        try:
            if eye is not None:self.camera(eye,target,up)
            result['capture']=self.capture(filename,width,height,required=False)
        finally:
            if eye is not None:
                try:viewport.camera=original;viewport.refresh()
                except Exception as exc:restore_error=str(exc)
            after=observe(self);comparison=changes(before,after)
            result.update(observation=comparison,camera_restore_error=restore_error,regeneration_performed=False,
                          claim='Revision/placement/parameter observations only; not exhaustive geometry equality or a model save.')
            result['status']='pass' if not comparison['model_changed'] and not restore_error and result.get('capture',{}).get('status')!='failed' else 'unproven'
            self.record('presentation',result)
        return result
    def apply_appearance(self,entity,appearance):
        # Accept an actual library/document Appearance object, not a guessed localized name.
        local=self.design.appearances.itemByName(appearance.name)
        if not local: local=self.design.appearances.addByCopy(appearance,appearance.name)
        entity.appearance=local
        return {'name':local.name}
    def color(self,entity,name,rgb,base_appearance):
        appearance=self.design.appearances.itemByName(name)
        if not appearance: appearance=self.design.appearances.addByCopy(base_appearance,name)
        prop=adsk.core.ColorProperty.cast(appearance.appearanceProperties.itemById('generic_diffuse'))
        if not prop: raise ValueError('Base appearance lacks generic_diffuse; select a compatible material.')
        if len(rgb)!=3 or any(not 0<=v<=255 for v in rgb): raise ValueError('RGB channels must be 0..255.')
        prop.value=adsk.core.Color.create(*[int(v) for v in rgb],255); entity.appearance=appearance
        return {'name':name,'rgb':rgb}
    @staticmethod
    def joint_motion(joint,motion):
        if motion not in ('rotation','slide'): raise ValueError('motion must be rotation or slide')
        raw=joint.jointMotion
        classes=([adsk.fusion.RevoluteJointMotion,adsk.fusion.CylindricalJointMotion] if motion=='rotation'
                 else [adsk.fusion.SliderJointMotion,adsk.fusion.CylindricalJointMotion])
        for cls in classes:
            typed=cls.cast(raw)
            if typed: return typed
        raise ValueError('Joint does not support requested rotation/slide motion.')
    def set_joint_limits(self,joint,minimum,maximum,motion='rotation',unit='deg'):
        self.check_cancel()
        if motion not in ('rotation','slide'): raise ValueError('motion must be rotation or slide')
        if minimum>maximum: raise ValueError('minimum exceeds maximum')
        limits=getattr(self.joint_motion(joint,motion),'rotationLimits' if motion=='rotation' else 'slideLimits')
        internal='rad' if motion=='rotation' else 'cm'
        values=[self.design.unitsManager.convert(v,unit,internal) for v in (minimum,maximum)]
        if any(not math.isfinite(v) for v in values): raise ValueError('Invalid joint limit units/values.')
        limits.isMinimumValueEnabled=False; limits.isMaximumValueEnabled=False
        limits.minimumValue=values[0]; limits.maximumValue=values[1]
        limits.isMinimumValueEnabled=True; limits.isMaximumValueEnabled=True
        return {'minimum':minimum,'maximum':maximum,'unit':unit}
    def sample_motion(self,joint,positions,pairs,motion='rotation',unit='deg',capture=False,
                      expected_world=None, translation_tolerance_mm=0.01,
                      rotation_tolerance=1e-6, near_contact_mm=None,
                      max_depth=4, max_samples=1000):
        """Verify joint AND expected root-context transforms before measuring.

        expected_world(position) returns [(root_context_occurrence, expected_matrix_array)].
        Expectations must come from independent kinematics, not the observed transform.
        Adaptive sampling requires this callable to cover intermediate positions as well.
        """
        if not callable(expected_world):
            raise ValueError('expected_world(position) is required for verified motion sampling')
        if motion not in ('rotation','slide'): raise ValueError('motion must be rotation or slide')
        if not positions or len(positions)>1000: raise ValueError('Provide 1..1000 sample positions')
        for p in positions: verification.finite(p, 'position')
        tt=verification.finite(translation_tolerance_mm,'translation tolerance',True)
        rt=verification.finite(rotation_tolerance,'rotation tolerance',True)
        prop='rotationValue' if motion=='rotation' else 'slideValue'
        internal='rad' if motion=='rotation' else 'cm'
        self.synchronize()  # Regenerate changed geometry once before pose-only checks.
        jm=self.joint_motion(joint,motion); initial=getattr(jm,prop); rows=[]
        monitored=[]
        def close(actual,expected):
            e=verification.matrix_error(actual,expected)
            return e['translation_mm']<=tt and e['rotation_entry_max']<=rt and e['homogeneous_entry_max']<=rt
        root_occurrences=model_tools.each(self.design.rootComponent.allOccurrences)
        # Collect all occurrences before moving: the callable may select different subsets.
        initial_world=[(o,list(o.transform2.asArray())) for o in root_occurrences]
        def evaluate(p):
            self.check_cancel()
            expectations=list(expected_world(p))
            if not expectations: raise ValueError('At least one expected occurrence transform is required')
            for o,matrix in expectations:
                if not any(o==root for root in root_occurrences):
                    raise ValueError('Expected occurrence must be resolved in root assembly context')
                verification.matrix_error(matrix,matrix)
                if not any(o==old for old in monitored): monitored.append(o)
            value=self.design.unitsManager.convert(p,unit,internal)
            verification.finite(value, 'converted position')
            setattr(jm,prop,value)
            def reached():
                return abs(getattr(jm,prop)-value)<=1e-6 and all(
                    close(o.transform2.asArray(),matrix) for o,matrix in expectations)
            # Pose changes use Fusion's joint solve/event processing, no full timeline regeneration.
            self.synchronize(reached,recompute=False)
            row={'requested':p,'unit':unit,'actual_internal':getattr(jm,prop),'checks':[],
                 'verified_world':[{'occurrence':model_tools.ref(o),
                    'expected_cm':list(matrix),'actual_cm':list(o.transform2.asArray()),
                    'error':verification.matrix_error(o.transform2.asArray(),matrix)} for o,matrix in expectations]}
            for one,two in pairs:
                row['checks'].append({'distance':self.minimum_distance(one,two),
                                      'interference':self.interference([one,two])})
            if not row['checks']: raise ValueError('Provide at least one measurement pair')
            row['clearance_mm']=min(c['distance']['distance_mm'] for c in row['checks'])
            row['collision']=any(c['interference']['count']>0 for c in row['checks'])
            if capture: row['frame']=self.capture('frame_%04d.png'%len(rows))
            rows.append(row); self.record('motion_samples',rows)
            return row
        restored=False
        try:
            if near_contact_mm is not None:
                report=verification.adaptive_samples(positions,evaluate,near_contact_mm,max_depth,max_samples)
            else:
                for p in positions: evaluate(p)
                xs=sorted(set(positions))
                report={'samples':rows,'unresolved_intervals':[
                    {'start':a,'end':b,'reason':'finite_sampling'} for a,b in zip(xs,xs[1:])],
                    'continuous_collision_proof':False}
        finally:
            # Restore even after cancellation; do not let a cancellation check skip restoration.
            try:
                self.guard(); setattr(jm,prop,initial)
                for _ in range(20):
                    self.guard()
                    restored=abs(getattr(jm,prop)-initial)<=1e-6 and all(
                        close(o.transform2.asArray(),matrix) for o,matrix in initial_world)
                    if restored: break
                    adsk.doEvents()
            except Exception as exc:
                self.warn('Pose restoration error: '+str(exc))
            self.result['pose_restored']=restored; self.flush()
            if not restored: self.warn('Pose restoration failed; inspect the assembly before continuing')
        if not restored: raise RuntimeError('Motion checks completed but original pose was not restored')
        return dict(report,pose_restored=restored,
                    limitation='Discrete samples only; unresolved intervals may contain collisions. Pose verification is limited to supplied independent expectations.')


def execute_job(store,job,app,design_getter,document_id_getter):
    request=job['request']; ctx=None; log=LimitedLog(); before=[];health_before=None;script_completed=False;post_checked=False;regenerated=False
    start=time.monotonic()
    result={'created':[],'measurements':{},'warnings':[],'files':[],'checkpoints':[],
            'traceback':None,'return_value':None,'validation':None}
    status='failed'
    try:
        from .compatibility import require_match
        if request.get('mode','modeling')!='read_only':require_match(request.get('_caller'))
        def guard():
            if document_id_getter()!=request['document_id']: raise ReferenceFailure('wrong_document','Active document ID changed; job target rejected.')
        guard(); d=design_getter()
        if request.get('mode','modeling')!='read_only':store.assert_no_uncertain_cloud()
        target=d.rootComponent if request['component_token']=='@root' else advanced.resolve(d,request['component_token'],adsk.fusion.Component)
        if request.get('mode','modeling')!='read_only': advanced.editable(d,target)
        ctx=Context(store,job,app,d,target,guard); result=ctx.result
        ctx.selection=scopes.Selection(d,request['scope'] if request.get('scope') is not None else (None if ctx.read_only else scopes.selected(d,target)))
        ctx.boundary=scopes.EditBoundary(d,ctx.selection,request.get('task'),target)
        if ctx.reconciliation:
            validate_reconciliation(ast.parse(request['script']))
            cloud.require_edit(app,d,request['document_id'],request.get('edit_token',''),
                               accepted_reference_versions=request.get('accepted_reference_versions'),
                               writer_id=request['task']['writer_id'])
        if not ctx.read_only:
            cloud.require_edit(app,d,request['document_id'],request.get('edit_token',''),
                               accepted_reference_versions=request.get('accepted_reference_versions'),
                               writer_id=request.get('task',{}).get('writer_id','legacy'))
            health_before=scopes.health_snapshot(d);ctx.health_baseline=health_before
            ctx.authoring=maintainability.Guard(store,d,ctx.selection,request.get('task'),
                getattr(getattr(app.activeDocument,'dataFile',None),'id',None) or request['document_id'],job['operation_id'])
            result['authoring']=ctx.authoring.status;ctx.flush()
        ctx.check_cancel()
        if ctx.read_only and not ctx.reconciliation: validate_read_only(ast.parse(request['script']))
        else: before=inventory(d,ctx.selection.components())
        if not ctx.read_only:
            from .recovery import observe
            try:result['before_observation']=observe(ctx);ctx.flush()
            except Exception as exc:result['observation_warning']=str(exc)
        if request['checkpoint_before']: ctx.checkpoint('before_batch')
        store.progress(job['job_id'],0,'Executing script on Fusion main thread')
        namespace={'__name__':'fusion_batch_job','__file__':str(ctx.output_dir/'script.py'),
                   'adsk':adsk,'app':app,'design':d,'target':target,'ctx':ctx}
        (ctx.output_dir/'script.py').write_text(request['script'],encoding='utf-8')
        with ctx.timed('script'), contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            exec(compile(request['script'],namespace['__file__'],'exec'),namespace)
            value=namespace['run'](ctx)
        json.dumps(value,allow_nan=False)
        result['return_value']=value;script_completed=True
        result['outcomes']['execution']='completed';ctx.flush()
        ctx.check_cancel()
        if not ctx.read_only:
            ctx.synchronize();regenerated=True
        if not ctx.read_only:
            result['edit_boundary']=ctx.boundary.post();post_checked=True
        if request['validate_after'] or not ctx.read_only:
            result['validation']=scopes.health_report(d,ctx.selection,health_before)
            if result['validation']['feature_errors'] or result['validation']['inspection_gaps'] or (request.get('scope') and result['validation']['evidence_status']!='pass'):
                raise RuntimeError('New/relevant feature damage or unavailable integrity checks; inspect validation')
        if result.get('edit_boundary',{}).get('violations'):
            raise RuntimeError('Observed changes exceeded permitted edit set; no automatic rollback')
        status='succeeded'
    except Cancelled as exc:
        status='cancelled'; result['message']=str(exc); result['traceback']=traceback.format_exc()
    except BaseException as exc:
        result['message']=str(exc); result['error_code']=getattr(exc,'code','execution_failure'); result['traceback']=traceback.format_exc()
    finally:
        if ctx and not ctx.read_only:
            from .recovery import observe,changes
            try:
                result['after_observation']=observe(ctx)
                result['change_observation']=changes(result.get('before_observation'),result['after_observation'])
            except Exception as exc:result['change_observation']={'model_changed':None,'status':'unproven','reason':str(exc)}
        result['stdout']=log.getvalue()
        result['execution_status']='completed' if script_completed else 'cancelled' if status=='cancelled' else 'failed'
        result['approval_status']='not_evaluated'
        result['regeneration_performed']=regenerated
        result['elapsed_seconds']=time.monotonic()-start
        result['operation_id']=job['operation_id'];result['task']=request.get('task')
        if ctx and ctx.boundary and not post_checked and health_before is not None:
            try:
                result['edit_boundary']=ctx.boundary.post()
                result['validation']=scopes.health_report(ctx.design,ctx.selection,health_before)
                if not regenerated and result['validation']['validation_status']=='pass':
                    result['validation']['validation_status']='unproven'
                    result['validation']['inspection_gaps'].append({'check':'final_regeneration','message':'Script failed/cancelled before final regeneration'})
            except Exception as exc:result['warnings'].append('Post-failure inspection unavailable: '+str(exc))
        if ctx:
            if ctx.authoring:
                try:
                    result['authoring']=ctx.authoring.finish(script_completed)
                    if result['authoring'].get('blocked'):status='failed'
                except Exception as exc:
                    result['authoring']={'status':'unproven','message':str(exc),'reconciliation_required':True};status='failed'
            result['recompute_policy']='read_only_no_regeneration' if ctx.read_only else 'modeling_final_regeneration'
            try:
                # Compare live API objects, not entityToken strings: Fusion may change token text.
                new=[] if ctx.read_only else [e for e in inventory(ctx.design,ctx.selection.components() if ctx.selection else None) if not any(e==old for old in before)]
                result['created_detected']=[model_tools.ref(e) for e in new]
            except Exception as exc: result['warnings'].append('Post-job inventory unavailable: '+str(exc))
            result['output_dir']=str(ctx.output_dir)
        result.setdefault('message',status)
        validation=result.get('validation') or {};boundary=result.get('edit_boundary') or {}
        result.setdefault('outcomes',{}).update(execution=result['execution_status'],
            mutation=result.get('change_observation',{}).get('model_changed','unobserved'),
            regeneration='completed' if regenerated else 'not_performed',
            integrity=validation.get('validation_status','not_checked'),
            edit_boundary='fail' if boundary.get('violations') else 'pass' if boundary.get('enforcement')=='narrow_preconditions_and_posthoc_detection' else 'unbounded',
            evidence=validation.get('evidence_status','not_checked'),
            authoring=result.get('authoring',{}).get('status','not_evaluated'))
        result['replay_permitted']=False
        result['partial_changes_possible']=status!='succeeded'
        store.finish(job['job_id'],status,result)
