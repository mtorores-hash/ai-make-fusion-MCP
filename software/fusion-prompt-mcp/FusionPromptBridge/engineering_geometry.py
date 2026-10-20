"""Bounded native geometry measurements. Temporary BRep only; never move design occurrences."""
import math
import adsk.core
import adsk.fusion
from . import advanced, model_tools, verification


def vector(v): return [v.x,v.y,v.z]
def unit(values):
    if len(values)!=3: raise ValueError('Expected three vector values')
    values=[verification.finite(x) for x in values]
    size=math.sqrt(sum(x*x for x in values))
    if size<1e-12: raise ValueError('Zero direction')
    return [x/size for x in values]
def angle(a,b):
    a=unit(a);b=unit(b)
    return math.degrees(math.acos(min(1,abs(sum(x*y for x,y in zip(a,b))))))
def point(values): return adsk.core.Point3D.create(*(verification.finite(x)/10 for x in values))
def body_of(e): return e if adsk.fusion.BRepBody.cast(e) else e.body

def signature(entity):
    """Declared metric signature, NOT complete shape equivalence."""
    e=advanced.native(entity);box=model_tools.bbox(e)
    result={'type':e.objectType,'bounds_mm':box['min_mm']+box['max_mm']}
    for attr,factor in [('area',100),('length',10),('volume',1000)]:
        if hasattr(e,attr):result[attr]=getattr(e,attr)*factor
    g=getattr(e,'geometry',None)
    if g:
        result['geometry_type']=g.objectType
        if hasattr(g,'radius'):result['radius_mm']=g.radius*10
        if adsk.core.Plane.cast(g):
            result['normal']=unit(vector(g.normal));result['plane_offset_mm']=sum(a*b for a,b in zip(result['normal'],model_tools.xyz(g.origin)))
    return result

def signature_changes(before,after,tolerances):
    """Every captured numeric field needs an explicit tolerance to authorize a changed signature."""
    changed=[]
    for key in before.keys()|after.keys():
        a=before.get(key);b=after.get(key)
        if a==b:continue
        tol=tolerances.get(key)
        numeric_pair=type(a) in (float,int) and type(b) in (float,int)
        list_pair=isinstance(a,list) and isinstance(b,list)
        if tol is not None and (numeric_pair or list_pair):
            tol=verification.finite(tol,key,True)
            av=a if isinstance(a,list) else [a];bv=b if isinstance(b,list) else [b]
            if len(av)==len(bv) and all(abs(verification.finite(x)-verification.finite(y))<=tol for x,y in zip(av,bv)):continue
        changed.append(key)
    return changed

def temporary_world(entity):
    """Copy native geometry and explicitly apply the root-context occurrence transform once."""
    manager=adsk.fusion.TemporaryBRepManager.get()
    temp=manager.copy(advanced.native(entity))
    if not temp:raise RuntimeError('Temporary BRep copy failed')
    occurrence=getattr(entity,'assemblyContext',None)
    if occurrence:
        if occurrence.assemblyContext:raise ValueError('Resolve occurrence in root assembly context before checking')
        if not manager.transform(temp,occurrence.transform2):raise RuntimeError('Temporary BRep transform failed')
    return temp

def overlap(a,b):
    if verification.separated_boxes(model_tools.bbox(a),model_tools.bbox(b)):
        return {'volume_mm3':0.0,'method':'disjoint_bounds','location_mm':None}
    manager=adsk.fusion.TemporaryBRepManager.get();candidate=manager.copy(a)
    if not candidate or not manager.booleanOperation(candidate,b,adsk.fusion.BooleanTypes.IntersectionBooleanType):
        raise RuntimeError('Intersection kernel result unavailable; not clear')
    volume=verification.finite(candidate.volume*1000,'intersection volume',True)
    location=None
    if volume>0:
        bounds=model_tools.bbox(candidate);location=[(a+b)/2 for a,b in zip(bounds['min_mm'],bounds['max_mm'])]
    return {'volume_mm3':volume,'location_mm':location,'method':'temporary_BRep_intersection'}

def envelope_box(box,translation_mm):
    low=box['min_mm'];high=box['max_mm']
    if len(low)!=3 or len(high)!=3 or len(translation_mm)!=3:raise ValueError('Box/translation needs xyz')
    size=[verification.finite(b)-verification.finite(a) for a,b in zip(low,high)]
    if min(size)<=0:raise ValueError('Envelope must have positive volume')
    margin=verification.finite(box.get('margin_mm',0),'envelope margin',True)
    center=[(a+b)/2+verification.finite(t) for a,b,t in zip(low,high,translation_mm)]
    spec=adsk.core.OrientedBoundingBox3D.create(point(center),adsk.core.Vector3D.create(1,0,0),
        adsk.core.Vector3D.create(0,1,0),*((x+2*margin)/10 for x in size))
    result=adsk.fusion.TemporaryBRepManager.get().createBox(spec)
    if not result:raise RuntimeError('Could not construct declared envelope')
    return result

def distance(app,a,b):
    measured=app.measureManager.measureMinimumDistance(a,b)
    if not measured:raise RuntimeError('Distance measurement unavailable')
    return {'gap_mm':verification.finite(measured.value*10,'gap',True),'points_mm':[model_tools.xyz(measured.positionOne),model_tools.xyz(measured.positionTwo)]}

def planar_wall(app,a,b,limits):
    if not adsk.core.Plane.cast(a.geometry) or not adsk.core.Plane.cast(b.geometry):
        raise ValueError('continuous_wall supports declared planar faces only')
    normal=unit(vector(a.geometry.normal))
    delta=[y-x for x,y in zip(model_tools.xyz(a.pointOnFace),model_tools.xyz(b.pointOnFace))]
    result=distance(app,a,b)
    result.update(step_mm=abs(sum(n*x for n,x in zip(normal,delta))),normal_angle_deg=angle(normal,vector(b.geometry.normal)))
    result['failed_metrics']=[key for key in ('step_mm','normal_angle_deg','gap_mm')
                              if result[key]>verification.finite(limits[key],key,True)]
    result['section_hint']={'origin_mm':result['points_mm'][0],'through_mm':result['points_mm'][1],
                            'note':'Inspect a section through these locations and the declared wall thickness; no section created.'}
    return result

def join_samples(a,b,limits,samples=5,curvature=False):
    if type(samples) is not int or not 3<=samples<=65:raise ValueError('Use 3..65 boundary samples')
    if getattr(a,'assemblyContext',None)!=getattr(b,'assemblyContext',None):
        raise ValueError('Shared-boundary sampling requires matching occurrence context')
    shared=[e for e in model_tools.each(a.edges) if any(advanced.native(e)==advanced.native(f) for f in model_tools.each(b.edges))]
    if not shared:raise ValueError('No common topological edge; use declared gap/wall check for disconnected faces')
    rows=[]
    for edge in shared:
        ok,start,end=edge.evaluator.getParameterExtents()
        if not ok:raise RuntimeError('Boundary parameter range unavailable')
        for i in range(samples):
            # Interior samples avoid vertex singularities. Endpoints remain explicitly untested.
            ok,p=edge.evaluator.getPointAtParameter(start+(end-start)*(i+0.5)/samples)
            if not ok:raise RuntimeError('Boundary point unavailable')
            ok1,n1=a.evaluator.getNormalAtPoint(p);ok2,n2=b.evaluator.getNormalAtPoint(p)
            if not ok1 or not ok2:raise RuntimeError('Boundary normal unavailable')
            row={'edge':model_tools.ref(edge),'location_mm':model_tools.xyz(p),'normal_angle_deg':angle(vector(n1),vector(n2))}
            row['failed']=row['normal_angle_deg']>verification.finite(limits['normal_angle_deg'],'angle tolerance',True)
            if curvature:
                spectra=[]
                for face in (a,b):
                    ok,uv=face.evaluator.getParameterAtPoint(p)
                    if not ok:raise RuntimeError('Surface parameter unavailable')
                    ok,t,kmax,kmin=face.evaluator.getCurvature(uv)
                    if not ok:raise RuntimeError('Curvature unavailable')
                    spectra.append(sorted([abs(verification.finite(kmax))/10,abs(verification.finite(kmin))/10]))
                row['curvature_magnitude_delta_per_mm']=max(abs(x-y) for x,y in zip(*spectra))
                row['failed']|=row['curvature_magnitude_delta_per_mm']>verification.finite(limits['curvature_per_mm'],'curvature tolerance',True)
            rows.append(row)
    return {'samples':rows,'failed_samples':sum(r['failed'] for r in rows),
            'not_checked':['vertices','between_samples','aesthetic_quality']+(['G2_orientation_and_signed_shape_operator'] if curvature else []),
            'claim':'Sampled tangent-plane agreement; curvature magnitudes can reject G2 but cannot establish it.'}
