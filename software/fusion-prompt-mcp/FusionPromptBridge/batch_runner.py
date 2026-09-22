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
from . import advanced, model_tools

class Cancelled(Exception): pass

class LimitedLog(io.TextIOBase):
    def __init__(self,limit=1_000_000): self.parts=[]; self.size=0; self.limit=limit; self.truncated=False
    def write(self,text):
        space=max(self.limit-self.size,0); self.parts.append(text[:space]); self.size+=min(len(text),space)
        self.truncated |= len(text)>space
        return len(text)
    def getvalue(self): return ''.join(self.parts)+ ('\n[log truncated]' if self.truncated else '')

def inventory(d):
    entities=[]
    for c in model_tools.each(d.allComponents):
        entities.append(c)
        for collection in (c.bRepBodies,c.sketches,c.features,c.joints,c.asBuiltJoints):
            entities.extend(model_tools.each(collection))
    return entities

class Context:
    def __init__(self,store,job,app,design,target,guard):
        self.store=store; self.job_id=job['job_id']; self.operation_id=job['operation_id']
        self.request=job['request']; self.app=app; self.design=design; self.target=target
        self.document=app.activeDocument; self.units=self.request['units']; self.guard=guard
        self.output_dir=store.root/'artifacts'/self.job_id
        self.output_dir.mkdir(parents=True,exist_ok=True)
        self.result={'created':[],'measurements':{},'warnings':[],'files':[],'checkpoints':[],
                     'traceback':None,'return_value':None,'validation':None}

    def check_cancel(self):
        self.guard()
        if self.store.row(self.job_id)['cancel_requested']: raise Cancelled('Cancellation requested at cooperative boundary.')

    def flush(self): self.store.partial(self.job_id,self.result)
    def progress(self,fraction,message):
        self.check_cancel(); self.store.progress(self.job_id,fraction,message); self.flush()
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
        p=self.design.userParameters.itemByName(name)
        if p: p.expression=expression
        else: p=self.design.userParameters.add(name,adsk.core.ValueInput.createByString(expression),unit or self.units,'Batch MCP')
        return p
    def select_edges(self,body,filters=None,feature=None): return model_tools.select(body,'edge',filters,feature)
    def select_faces(self,body,filters=None,feature=None): return model_tools.select(body,'face',filters,feature)
    @staticmethod
    def expect_one(matches):
        if len(matches)!=1: raise ValueError('Expected exactly one geometry match; got '+str(len(matches)))
        return matches[0]
    def inspect(self,include_topology=False): return model_tools.inspect_full(self.design,include_topology)
    def validate(self): return model_tools.validate(self.design)
    def minimum_distance(self,one,two): return model_tools.measure(self.app,self.design,one,two)
    def interference(self,references): return model_tools.interference(self.design,references)
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
    def export(self,filename,entity=None):
        self.check_cancel(); path=self.path(filename); manager=self.design.exportManager
        suffix=path.suffix.lower(); entity=entity or self.target
        if suffix=='.f3d': opts=manager.createFusionArchiveExportOptions(str(path),entity)
        elif suffix in ('.step','.stp'): opts=manager.createSTEPExportOptions(str(path),entity)
        elif suffix=='.stl':
            opts=manager.createSTLExportOptions(entity,str(path)); opts.sendToPrintUtility=False
        else: raise ValueError('Supported exports: f3d, step, stp, stl.')
        if not manager.execute(opts) or not path.exists(): raise RuntimeError('Fusion export failed: '+filename)
        return self.artifact(path)
    def checkpoint(self,label):
        self.check_cancel()
        clean=re.sub(r'[^A-Za-z0-9_-]+','_',label)[:70] or 'checkpoint'
        filename='checkpoint_%03d_%s.f3d'%(len(self.result['checkpoints']),clean)
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
    def capture(self,filename='view.png',width=1920,height=1080):
        self.check_cancel()
        if not 1<=width<=8192 or not 1<=height<=8192: raise ValueError('Invalid image dimensions.')
        path=self.path(filename)
        if path.suffix.lower()!='.png': raise ValueError('Use a PNG filename.')
        if not self.app.activeViewport.saveAsImageFile(str(path),width,height): raise RuntimeError('Capture failed.')
        size=model_tools.png_dimensions(path)
        if size!=(width,height): raise RuntimeError('Fusion returned unexpected image dimensions: '+str(size))
        return self.artifact(path)
    def camera(self,eye,target,up=(0,0,1),fit=False):
        self.check_cancel(); viewport=self.app.activeViewport; camera=viewport.camera
        camera.eye=self.point(*eye); camera.target=self.point(*target)
        camera.upVector=adsk.core.Vector3D.create(*up); camera.isFitView=fit
        camera.isSmoothTransition=False; viewport.camera=camera; viewport.refresh()
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
    def sample_motion(self,joint,positions,pairs,motion='rotation',unit='deg',capture=False):
        if motion not in ('rotation','slide'): raise ValueError('motion must be rotation or slide')
        if not positions or len(positions)>1000: raise ValueError('Provide 1..1000 sample positions.')
        prop='rotationValue' if motion=='rotation' else 'slideValue'
        internal='rad' if motion=='rotation' else 'cm'
        jm=self.joint_motion(joint,motion); initial=getattr(jm,prop); rows=[]
        restored=False
        try:
            for i,p in enumerate(positions):
                self.check_cancel(); value=self.design.unitsManager.convert(p,unit,internal)
                if not math.isfinite(value): raise ValueError('Invalid motion sample.')
                setattr(jm,prop,value)
                if not self.design.computeAll(): raise RuntimeError('Compute failed during motion sampling.')
                actual=getattr(jm,prop)
                if abs(actual-value)>1e-6: raise RuntimeError('Joint did not reach requested sample pose.')
                row={'requested':p,'unit':unit,'actual_internal':actual,'checks':[]}
                for one,two in pairs:
                    row['checks'].append({'distance':self.minimum_distance(one,two),
                                          'interference':self.interference([one,two])})
                if capture: row['frame']=self.capture('frame_%04d.png'%i)
                rows.append(row); self.record('motion_samples',rows)
        finally:
            setattr(jm,prop,initial)
            restored=bool(self.design.computeAll()) and abs(getattr(jm,prop)-initial)<=1e-6
            if not restored: self.warn('Pose restoration failed; inspect the assembly.')
        return {'samples':rows,'pose_restored':restored,
                'limitation':'Discrete samples only; collisions between sample positions are not excluded.'}


def execute_job(store,job,app,design_getter,document_id_getter):
    request=job['request']; ctx=None; log=LimitedLog(); before=[]
    result={'created':[],'measurements':{},'warnings':[],'files':[],'checkpoints':[],
            'traceback':None,'return_value':None,'validation':None}
    status='failed'
    try:
        def guard():
            if document_id_getter()!=request['document_id']: raise ValueError('Active document ID changed; job target rejected.')
        guard(); d=design_getter()
        target=advanced.resolve(d,request['component_token'],adsk.fusion.Component)
        advanced.editable(d,target)
        ctx=Context(store,job,app,d,target,guard); result=ctx.result
        ctx.check_cancel(); before=inventory(d)
        if request['checkpoint_before']: ctx.checkpoint('before_batch')
        store.progress(job['job_id'],0,'Executing script on Fusion main thread')
        namespace={'__name__':'fusion_batch_job','__file__':str(ctx.output_dir/'script.py'),
                   'adsk':adsk,'app':app,'design':d,'target':target,'ctx':ctx}
        (ctx.output_dir/'script.py').write_text(request['script'],encoding='utf-8')
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            exec(compile(request['script'],namespace['__file__'],'exec'),namespace)
            value=namespace['run'](ctx)
        json.dumps(value,allow_nan=False)
        result['return_value']=value
        ctx.check_cancel()
        if not d.computeAll(): raise RuntimeError('Fusion computeAll reported failure after script.')
        if request['validate_after']:
            result['validation']=ctx.validate()
            if result['validation']['feature_errors']: raise RuntimeError('Model built, but feature/joint errors remain. Inspect validation.')
        status='succeeded'
    except Cancelled as exc:
        status='cancelled'; result['message']=str(exc); result['traceback']=traceback.format_exc()
    except BaseException as exc:
        result['message']=str(exc); result['traceback']=traceback.format_exc()
    finally:
        result['stdout']=log.getvalue()
        if ctx:
            try:
                # Compare live API objects, not entityToken strings: Fusion may change token text.
                new=[e for e in inventory(ctx.design) if not any(e==old for old in before)]
                result['created_detected']=[model_tools.ref(e) for e in new]
            except Exception as exc: result['warnings'].append('Post-job inventory unavailable: '+str(exc))
            result['output_dir']=str(ctx.output_dir)
        result.setdefault('message',status)
        result['partial_changes_possible']=status!='succeeded'
        store.finish(job['job_id'],status,result)
