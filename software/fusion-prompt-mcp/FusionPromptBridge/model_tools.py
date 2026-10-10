"""Helpers available both to batch scripts and typed inspection tools. All calls on UI thread."""
import math
from pathlib import Path
import struct
import adsk.core
import adsk.fusion
from . import advanced, verification
from . import scope as scopes

def each(c): return [c.item(i) for i in range(c.count)]
def xyz(p): return [p.x*10, p.y*10, p.z*10]
def ref(e): return advanced.ref(e)
def bbox(e):
    b=e.boundingBox
    return {'min_mm':xyz(b.minPoint),'max_mm':xyz(b.maxPoint),
            'size_mm':[(getattr(b.maxPoint,a)-getattr(b.minPoint,a))*10 for a in ('x','y','z')]}

def topology(body):
    result={'reference':ref(body),'bounds':bbox(body),'is_solid':body.isSolid,
            'volume_mm3':body.volume*1000, 'faces':[], 'edges':[]}
    for f in each(body.faces):
        surface=f.geometry
        row={'reference':ref(f),'surface':surface.objectType,'area_mm2':f.area*100,
             'point_mm':xyz(f.pointOnFace),'bounds':bbox(f)}
        if hasattr(surface,'radius'): row['radius_mm']=surface.radius*10
        if adsk.core.Plane.cast(surface): row['plane_normal']=[surface.normal.x,surface.normal.y,surface.normal.z]
        row['edge_references']=[ref(e) for e in each(f.edges)]
        result['faces'].append(row)
    for e in each(body.edges):
        curve=e.geometry
        row={'reference':ref(e),'curve':curve.objectType,'length_mm':e.length*10,
             'point_mm':xyz(e.pointOnEdge),'bounds':bbox(e)}
        if hasattr(curve,'radius'): row['radius_mm']=curve.radius*10
        if e.startVertex: row['start_mm']=xyz(e.startVertex.geometry)
        if e.endVertex: row['end_mm']=xyz(e.endVertex.geometry)
        result['edges'].append(row)
    return result

def inspect_full(d, include_topology=False, offset=0, limit=None, scope=None, include_context=False):
    selection=scopes.Selection(d,scope) if scope is not None else None
    warnings=[]
    components=[]
    all_components=selection.components() if selection else each(d.allComponents)
    if offset < 0 or (limit is not None and not 1 <= limit <= 100): raise ValueError('Invalid page bounds.')
    selected=all_components[offset:offset+limit if limit is not None else None]
    for c in selected:
        row={'revision':c.revisionId,'reference':ref(c),'bodies':[],'features':[],'sketches':[],'joints':[]}
        for b in each(c.bRepBodies):
            try:
                row['bodies'].append(topology(b) if include_topology else
                    {'reference':ref(b),'bounds':bbox(b),'is_solid':b.isSolid,
                     'volume_mm3':b.volume*1000,'face_count':b.faces.count,'edge_count':b.edges.count})
            except Exception as exc: warnings.append('Body '+b.name+': '+str(exc))
        for f in each(c.features):
            row['features'].append(advanced.health(f))
        for s in each(c.sketches):
            row['sketches'].append({'reference':ref(s),'fully_constrained':s.isFullyConstrained,
                'dimensions':[{'name':dim.parameter.name,'expression':dim.parameter.expression}
                              for dim in each(s.sketchDimensions)],
                'constraint_count':s.geometricConstraints.count})
        for collection in (c.joints,c.asBuiltJoints):
            for j in each(collection): row['joints'].append(advanced.health(j))
        components.append(row)
    occurrences=[]
    for o in each(d.rootComponent.allOccurrences) if include_context or offset==0 else []:
        if selection and not selection.contains(advanced.native(o.component)):continue
        occurrences.append({'reference':{'token':o.entityToken,'occurrence_token':''},
            'path':o.fullPathName,'component':ref(o.component),'grounded':o.isGrounded,
            'linked':o.isReferencedComponent,'transform_cm':o.transform2.asArray()})
    return {'components':components,'occurrences':occurrences,
            'total_components':len(all_components),'offset':offset,
            'next_offset':offset+len(selected) if offset+len(selected)<len(all_components) else None,
            'scope':selection.report() if selection else 'full_design',
            'context_included':include_context or offset==0,
            'parameters':[{'name':p.name,'expression':p.expression,'unit':p.unit} for p in each(d.allParameters)
                          if (include_context or offset==0) and (not selection or p.name in selection.spec.get('parameter_names',[]))],
            'coordinate_notes':'Component geometry is local mm. Occurrence transform2 matrices use Fusion cm.',
            'topology_included':include_topology,'warnings':warnings,'complete':not warnings}

def resolve_ref(d, reference, world=False):
    if isinstance(reference,str): reference={'token':reference}
    e=advanced.resolve(d,reference['token'])
    context=reference.get('occurrence_token','')
    if context:
        o=advanced.resolve(d,context,adsk.fusion.Occurrence)
        e=advanced.native(e)
        if adsk.fusion.Occurrence.cast(e):
            return e.createForAssemblyContext(o)
        owner=e.parentComponent if adsk.fusion.BRepBody.cast(e) else e.body.parentComponent
        if o.component != owner: raise ValueError('Reference/occurrence mismatch.')
        e=e.createForAssemblyContext(o)
    elif world and not getattr(e,'assemblyContext',None):
        owner=getattr(e,'parentComponent',None) or getattr(getattr(e,'body',None),'parentComponent',None)
        if owner and owner != d.rootComponent:
            raise ValueError('World-space check needs an occurrence_token for component geometry.')
    return e

def parallel(vector, axis, angular_tolerance_deg):
    norm=math.sqrt(sum(v*v for v in vector)); anorm=math.sqrt(sum(v*v for v in axis))
    if not norm or not anorm: return False
    dot=abs(sum(v*a for v,a in zip(vector,axis)) / (norm*anorm))
    return dot >= math.cos(math.radians(angular_tolerance_deg))

def select(body, kind='edge', filters=None, feature=None):
    """Return ALL matches; no implicit first match. Geometric predicates are component-local."""
    filters=filters or {}
    allowed={'geometry_type','parallel_to','normal_parallel_to','length_mm','radius_mm','area_mm2',
             'within_box_mm','at_coordinate_mm','tolerance_mm','angular_tolerance_deg'}
    unknown=set(filters)-allowed
    if unknown: raise ValueError('Unknown filters: '+str(sorted(unknown)))
    tol=float(filters.get('tolerance_mm',0.05)); angle=float(filters.get('angular_tolerance_deg',1))
    if tol < 0 or not math.isfinite(tol) or not 0 <= angle <= 90: raise ValueError('Invalid tolerance.')
    entities=each(body.edges if kind=='edge' else body.faces)
    if kind not in ('edge','face'): raise ValueError('kind must be edge or face.')
    if feature:
        # Current faces associated with a feature; not historical edge indices.
        source_faces=each(feature.faces)
        members=source_faces if kind=='face' else [e for f in source_faces for e in each(f.edges)]
        entities=[e for e in entities if any(e==m for m in members)]
    matches=[]
    for e in entities:
        g=e.geometry
        if 'geometry_type' in filters and g.objectType.split('::')[-1] != filters['geometry_type']: continue
        if 'parallel_to' in filters:
            if kind!='edge' or not adsk.core.Line3D.cast(g): continue
            if not parallel([g.direction.x,g.direction.y,g.direction.z],filters['parallel_to'],angle): continue
        if 'normal_parallel_to' in filters:
            if kind!='face' or not adsk.core.Plane.cast(g): continue
            if not parallel([g.normal.x,g.normal.y,g.normal.z],filters['normal_parallel_to'],angle): continue
        rejected=False
        for key,attr,scale in [('length_mm','length',10),('area_mm2','area',100),('radius_mm','radius',10)]:
            if key not in filters: continue
            source=g if key=='radius_mm' else e
            if not hasattr(source,attr): rejected=True; break
            value=getattr(source,attr)*scale; interval=filters[key]
            if len(interval)!=2 or interval[0]>interval[1]: raise ValueError('Range needs [min,max].')
            if not interval[0]-tol <= value <= interval[1]+tol: rejected=True; break
        if rejected: continue
        box=bbox(e)
        if 'within_box_mm' in filters:
            region=filters['within_box_mm']
            if len(region)!=2 or any(len(v)!=3 for v in region): raise ValueError('Box needs two xyz corners.')
            if any(box['min_mm'][i]<region[0][i]-tol or box['max_mm'][i]>region[1][i]+tol for i in range(3)): continue
        if 'at_coordinate_mm' in filters:
            coords=filters['at_coordinate_mm']
            if any(k not in ('x','y','z') for k in coords): raise ValueError('Coordinate keys are x/y/z.')
            if any(abs(box['min_mm']['xyz'.index(k)]-v)>tol or abs(box['max_mm']['xyz'.index(k)]-v)>tol
                   for k,v in coords.items()): continue
        matches.append(e)
    return matches

def measure(app,d,one,two):
    a=resolve_ref(d,one,True); b=resolve_ref(d,two,True)
    m=app.measureManager.measureMinimumDistance(a,b)
    if not m: raise RuntimeError('Fusion minimum-distance measurement returned no result.')
    return {'distance_mm':m.value*10,'point_one_mm':xyz(m.positionOne),'point_two_mm':xyz(m.positionTwo),
            'note':'Zero distance alone does not distinguish touching from penetration.'}

def interference(d,references):
    if len(references)<2: raise ValueError('At least two body or occurrence references required.')
    resolved=[resolve_ref(d,r,True) for r in references]
    if len(resolved)==2 and all(adsk.fusion.BRepBody.cast(e) and
            not getattr(e,'assemblyContext',None) and e.parentComponent==d.rootComponent for e in resolved):
        if verification.separated_boxes(bbox(resolved[0]),bbox(resolved[1])):
            return {'interferences':[],'count':0,'checked':True,'method':'root_body_AABB_separation',
                    'note':'Strictly disjoint body bounds at this pose; no tolerance or path guarantee.'}
    entities=adsk.core.ObjectCollection.create()
    for e in resolved: entities.add(e)
    inp=d.createInterferenceInput(entities)
    inp.areCoincidentFacesIncluded=False
    results=d.analyzeInterference(inp)
    if results is None: raise RuntimeError('Interference analysis unavailable for this design/API state.')
    rows=[]
    for r in each(results):
        rows.append({'one':ref(r.entityOne),'two':ref(r.entityTwo),
                     'volume_mm3':r.interferenceBody.volume*1000 if r.interferenceBody else None})
    return {'interferences':rows,'count':len(rows),'checked':True,
            'note':'Current pose only. No tolerance envelope or insertion path inferred.'}

def validate(d, scope=None, baseline=None):
    selection=scopes.Selection(d,scope)
    return scopes.health_report(d,selection,baseline)


def png_dimensions(path):
    with Path(path).open('rb') as f: header=f.read(24)
    if header[:8]!=b'\x89PNG\r\n\x1a\n': raise ValueError('Expected PNG output.')
    return struct.unpack('>II',header[16:24])
