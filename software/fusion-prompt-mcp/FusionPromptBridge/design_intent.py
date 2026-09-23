"""Native body-backed semantic selectors and bounded surface review candidates."""
import json
import math
from . import advanced, model_tools, verification

GROUP='AI_MAKE_MCP_INTENT'


def tag_geometry(design, body, name, kind, filters, feature=None, role='functional', requirement=''):
    if not name or name.startswith('_'): raise ValueError('Use a nonempty semantic name')
    body=advanced.native(body)
    # A semantic name is unique across component definitions. Repeated occurrences share it.
    for component in model_tools.each(design.allComponents):
        for candidate in model_tools.each(component.bRepBodies):
            if candidate!=body and candidate.attributes.itemByName(GROUP,name):
                raise ValueError('Semantic name already exists on another body')
    matches=model_tools.select(body,kind,filters,feature)
    if len(matches)!=1: raise ValueError('Semantic selector must match exactly one current entity')
    definition={'kind':kind,'filters':filters,'feature_token':feature.entityToken if feature else '',
                'role':role,'requirement':requirement}
    if not body.attributes.add(GROUP,name,json.dumps(definition,allow_nan=False)):
        raise RuntimeError('Fusion could not store semantic selector')
    return dict(definition,name=name,entity=model_tools.ref(matches[0]))


def resolve_tag(design, name):
    found=[]
    for component in model_tools.each(design.allComponents):
        for body in model_tools.each(component.bRepBodies):
            attr=body.attributes.itemByName(GROUP,name)
            if attr: found.append((body,json.loads(attr.value)))
    if len(found)!=1: raise ValueError('Missing or ambiguous semantic tag: '+name)
    body,definition=found[0]
    feature=advanced.resolve(design,definition['feature_token']) if definition['feature_token'] else None
    matches=model_tools.select(body,definition['kind'],definition['filters'],feature)
    if len(matches)!=1: raise ValueError('Semantic tag no longer resolves uniquely: '+name)
    return matches[0]


def surface_audit(body, short_edge_mm, small_face_mm2, slender_width_mm, protected_entities=()):
    """Review candidates only. Width is 2*area/perimeter, NOT minimum wall thickness.

    No normal/curvature continuity or full thin-region claim is made by this audit.
    protected_entities are actual re-resolved entities, never index/token comparisons.
    """
    thresholds={'short_edge_mm':verification.finite(short_edge_mm,'short_edge_mm',True),
                'small_face_mm2':verification.finite(small_face_mm2,'small_face_mm2',True),
                'slender_width_mm':verification.finite(slender_width_mm,'slender_width_mm',True)}
    findings=[]
    def add(entity,kind,value,unit,threshold):
        intentional=any(entity==p for p in protected_entities)
        findings.append({'entity':model_tools.ref(entity),'kind':kind,'value':value,'unit':unit,
                         'threshold':threshold,'location_mm':model_tools.xyz(
                            entity.pointOnEdge if kind=='short_edge' else entity.pointOnFace),
                         'intentional':intentional,'status':'functional_review' if intentional else 'review_candidate'})
    for edge in model_tools.each(body.edges):
        length=edge.length*10
        if length<thresholds['short_edge_mm']: add(edge,'short_edge',length,'mm',short_edge_mm)
    for face in model_tools.each(body.faces):
        area=face.area*100
        if area<thresholds['small_face_mm2']: add(face,'small_face',area,'mm2',small_face_mm2)
        perimeter=sum(e.length*10 for e in model_tools.each(face.edges))
        if perimeter>0:
            width=2*area/perimeter
            if width<thresholds['slender_width_mm']: add(face,'slender_face_indicator',width,'mm',slender_width_mm)
    return {'findings':findings,'thresholds':thresholds,'coordinate_system':'body assembly context, mm',
            'automatic_modifications':False,'complete_surface_audit':False,
            'not_checked':['minimum_wall_thickness','near_coincident_surfaces','G0_G1_G2_continuity',
                           'unsupported_layers','support_removal','physical_print_performance']}
