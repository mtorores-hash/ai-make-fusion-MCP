"""Revision-bound manufacturing declarations, separate from slicer verification."""
import adsk.fusion
from . import advanced, engineering, engineering_geometry as geom, model_tools, verification


def identity(ctx,entity):
    """Bounded identity for one native body or a leaf component export."""
    if getattr(entity,'assemblyContext',None):raise ValueError('Export identity requires native coordinates, not an occurrence proxy')
    entity=advanced.native(entity)
    if adsk.fusion.BRepBody.cast(entity):bodies=[entity]
    elif adsk.fusion.Component.cast(entity):
        if entity.occurrences.count:raise ValueError('Manufacturing identity requires an individual leaf part, not a nested assembly')
        bodies=list(model_tools.each(entity.bRepBodies))
    else:raise ValueError('Export identity requires native body or leaf component')
    if not bodies or any(not b.isValid or not b.isSolid for b in bodies):raise ValueError('Export identity needs valid solid bodies')
    return {'document_id':ctx.request['document_id'],'entity':model_tools.ref(entity),
            'frame':'native_component_cm','bodies':[
                {'reference':model_tools.ref(b),'revision':b.revisionId,'signature':geom.signature(b)} for b in bodies]}


def handoff(ctx,entries,spec):
    """No inferred printability or slicer setting. Reject stale source geometry/bytes."""
    if spec.get('version')!='1.0':raise ValueError('manufacturing.version must be 1.0')
    session=engineering.Session(ctx,spec['interface_plan'])
    descriptors=spec['parts'];rows=[]
    for entry in entries:
        source=entry.get('geometry_identity')
        if not source:raise ValueError('Use export(capture_identity=True) to capture generation-time identity')
        if source['document_id']!=ctx.request['document_id']:raise ValueError('Export belongs to another document')
        target=model_tools.resolve_ref(ctx.design,source['entity'])
        if identity(ctx,target)!=source:raise ValueError('Stale exported geometry: '+entry['path'])
        if verification.file_hash(entry['path'])!=entry['sha256']:raise ValueError('Export bytes changed')
        part=descriptors[entry['path']]
        # Rigid orientation described by orthonormal bed-frame axes in native coordinates.
        orientation=part['print_orientation'];x=geom.unit(orientation['x_axis']);z=geom.unit(orientation['z_axis'])
        if abs(sum(a*b for a,b in zip(x,z)))>1e-6:raise ValueError('Print axes must be orthogonal')
        if orientation.get('frame')!='native_component':raise ValueError('Print orientation frame must be native_component')
        protected=part['protected_interfaces'];bed=part['bed_contact_face'];supports=part['allowed_support_faces']
        if not protected:raise ValueError('Explicit protected mating interfaces required')
        members=[model_tools.resolve_ref(ctx.design,b['reference']) for b in source['bodies']]
        resolved={}
        for name in set(protected+[bed]+supports):
            entity=session.resolve(name)
            if not any(advanced.native(geom.body_of(entity))==b for b in members):raise ValueError('Handoff interface outside exported part: '+name)
            if name==bed or name in supports:
                if not adsk.fusion.BRepFace.cast(entity):raise ValueError('Bed/support references must identify faces')
            if name in protected and not session.interfaces[name].get('protected'):raise ValueError('Mark protected interfaces in interface plan')
            resolved[name]=session.records[name]
        for name in ('support_exceptions','overhangs','bridges','access_constraints'):
            if name not in part:raise ValueError('Explicit '+name+' required; use an empty list with review status if none')
        review=part['geometry_review']
        if review.get('status') not in ('observed','unproven') or not review.get('source'):
            raise ValueError('Declare observed/unproven geometry review and source; no implicit pass')
        protected_metrics=session.protected()
        rows.append({'artifact':entry['path'],'sha256':entry['sha256'],'geometry_identity':source,
                     'declaration':part,'resolved_interfaces':resolved,
                     'protected_metrics':{name:protected_metrics[name] for name in protected}})
    return {'schema':'1.0','parts':rows,'manufacturing_readiness':'unproven','slicer_inspection':'required',
            'claim':'Revision/byte-matched declarations, not computed printability or approval.',
            'not_checked':['actual_bed_contact_after_orientation','automatic_overhang_or_bridge_detection',
                           'slicer_supports','support_removal','printer_profile','plate_arrangement','per_object_settings']}
