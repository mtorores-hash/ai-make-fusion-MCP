"""Bounded native revision/geometry attribution, never volume-only shape equivalence."""
from . import advanced, engineering_geometry as geom, verification

ROUND_OFF={'volume':1e-9,'area':1e-10,'bounds_mm':1e-9,'length':1e-9}

def each(c):return [c.item(i) for i in range(c.count)]

def component_state(component):
    result={'bodies':[],'collections':{},'gaps':[]}
    try:
        for body in each(component.bRepBodies):
            result['bodies'].append((body,body.revisionId,geom.signature(body)))
        for name in ('sketches','features','meshBodies','constructionPlanes','constructionAxes','constructionPoints','joints','asBuiltJoints'):
            result['collections'][name]=each(getattr(component,name))
    except Exception as exc:result['gaps'].append(str(exc))
    return result

def compare(before,after,tolerances=None):
    changes=[];limits=dict(ROUND_OFF);limits.update(tolerances or {})
    if before['gaps'] or after['gaps']:return {'status':'unproven','gaps':before['gaps']+after['gaps']}
    for name,objects in before['collections'].items():
        now=after['collections'][name]
        if len(objects)!=len(now) or any(not any(e==x for x in now) for e in objects):changes.append(name)
    if len(before['bodies'])!=len(after['bodies']):changes.append('body_count')
    for body,revision,signature in before['bodies']:
        matches=[(b,r,s) for b,r,s in after['bodies'] if b==body]
        if len(matches)!=1:changes.append('body_identity');continue
        _,now_revision,now_signature=matches[0]
        if now_revision!=revision:changes.append('body_revision')
        changes.extend(geom.signature_changes(signature,now_signature,limits))
    # Membership cannot establish unchanged sketch/feature/joint definitions. Only
    # history-free B-rep references qualify for propagation attribution here.
    opaque=any(before['collections'].values()) or any(after['collections'].values())
    status='fail' if changes else 'pass' if before['bodies'] and not opaque else 'unproven'
    return {'status':status,'changed':sorted(set(changes)),'numerical_limits':limits,
            'claim':'History-free B-rep identity/revision plus bounded metrics. Not complete shape equivalence; authored history, sketches, meshes, construction and joints remain unproven.'}

def generated_owner(parameter):
    """Only a native ModelParameter with an attributable creating object qualifies."""
    if not getattr(parameter,'createdBy',None):return None
    return getattr(parameter,'component',None)

def placement_changed(before,after,translation_mm=1e-8,rotation_entry=1e-10):
    e=verification.matrix_error(before,after)
    return e['translation_mm']>translation_mm or e['rotation_entry_max']>rotation_entry or e['homogeneous_entry_max']>rotation_entry
