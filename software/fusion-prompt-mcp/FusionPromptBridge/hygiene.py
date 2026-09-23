"""Read-only parametric hygiene audit. Reports unknowns; never repairs geometry."""
import re
import adsk.fusion
from . import advanced
from .modeling_rules import get_rules

DEFAULT_NAME=re.compile(r'^(Sketch|Body|Component|Plane|Axis|Point|Extrude|Fillet|Chamfer|Hole|Revolve|Sweep|Loft|Mirror|Pattern|Move|Joint)\s*\d+(?::\d+)?$',re.I)
MANUAL_REVIEW=[
    'Correct component activation/ownership and documented root-body exceptions',
    'Origin anchoring and constraint intent (fully constrained does not prove this)',
    'Driving parameter use, intentional constants, duplicate values and circularity',
    'Observed parameter perturbation/extreme-value test and restoration',
    'Projection/reference stability and intended parent-child relationships',
    'Feature order, repair-feature avoidance, timeline grouping/end-marker position',
    'Joint/grounding intent, stale assembly contexts and external-link ownership',
    'Configuration/derive suitability, save/version description and protected interfaces',
]


def audit(design):
    rules=get_rules()
    findings=[]; unknown=[]; counts={'components':0,'bodies':0,'sketches':0,'features':0,'joints':0,'parameters':0}
    def reference(entity):
        # Parameters and some timeline objects have no entityToken. Never invent one.
        result={}
        for attr,key in [('name','name'),('objectType','type'),('entityToken','token')]:
            try: result[key]=getattr(entity,attr)
            except Exception: pass
        return result
    def unavailable(entity,check,exc):
        unknown.append({'check':check,'entity':reference(entity),'message':str(exc)})
    def read(entity,attribute):
        try:
            value=getattr(entity,attribute)
            if value is None: raise ValueError(attribute+' returned no value')
            return value
        except Exception as exc:
            unavailable(entity,attribute,exc);return None
    def each(owner,attribute):
        try:
            collection=getattr(owner,attribute)
            return [collection.item(i) for i in range(collection.count)]
        except Exception as exc:
            unavailable(owner,attribute,exc);return []
    def finding(rule,severity,entity,message,**details):
        findings.append(dict(rule_id=rule,severity=severity,entity=reference(entity),message=message,**details))
    def name_check(entity,prefix=None):
        name=read(entity,'name')
        if name is None:return
        if not name.strip() or DEFAULT_NAME.fullmatch(name):
            finding('NAME_REQUIRED','error',entity,'Name this object by design purpose; default or empty name detected.')
        elif prefix and not name.startswith(prefix):
            finding('NAME_STYLE','review',entity,'Review the preferred naming prefix.',expected_prefix=prefix)
    def health(entity):
        value=read(entity,'healthState')
        if value is None:return
        states=adsk.fusion.FeatureHealthStates
        if value in (states.ErrorFeatureHealthState,states.WarningFeatureHealthState):
            finding('TIMELINE_HEALTH','error',entity,'Resolve the warning/error before completion.',
                    health=str(value),detail=read(entity,'errorOrWarningMessage'))
        elif value!=states.HealthyFeatureHealthState:
            finding('TIMELINE_STATE','review',entity,'Review non-healthy/suppressed/rolled-back state.',health=str(value))
    mode=read(design,'designType')
    if mode is not None and mode!=adsk.fusion.DesignTypes.ParametricDesignType:
        finding('PARAMETRIC_HISTORY','error',design,'Native parametric authoring requires design history; preserve imported source and review conversion explicitly.')
    root=read(design,'rootComponent')
    components=each(design,'allComponents')
    if not components:
        unavailable(design,'allComponents','No component definitions were returned')
    for component in components:
        counts['components']+=1
        if component!=root:name_check(component)
        for body in each(component,'bRepBodies'):
            counts['bodies']+=1;name_check(body)
            if component==root:
                finding('ROOT_BODY','review',body,'Root body: document the single-part/concept exception or model in an owned component.')
        for sketch in each(component,'sketches'):
            counts['sketches']+=1;name_check(sketch,'sk_');health(sketch)
            constrained=read(sketch,'isFullyConstrained')
            if constrained is False:
                finding('SKETCH_CONSTRAINTS','error',sketch,'Sketch is not fully constrained.')
            curves=each(sketch,'sketchCurves');dimensions=each(sketch,'sketchDimensions')
            curve_count=len(curves);dimension_count=len(dimensions)
            if curve_count>20 or dimension_count>10:
                finding('SKETCH_COMPLEXITY','review',sketch,'Review sketch size; counts are heuristics, not validity limits.',
                        curves=curve_count,dimensions=dimension_count,
                        review_band='very_large' if curve_count>=250 else 'large' if curve_count>=100 else 'above_guideline')
            # Fixed state is available on sketch entities, not inferred from fully-constrained state.
            fixed_count=0
            for curve in curves:
                if read(curve,'isFixed') is True:fixed_count+=1
            points=each(sketch,'sketchPoints')
            origin=read(sketch,'originPoint') if points else None
            for point in points:
                # The origin is expected to be fixed and is not a misuse of Fix.
                if point!=origin and read(point,'isFixed') is True:fixed_count+=1
            if fixed_count:
                finding('FIX_USAGE','review',sketch,'Review fixed entities; allow intentional spline/text exceptions, not a substitute for constraints.',fixed_entities=fixed_count)
        for collection,prefix in [('constructionPlanes','pl_'),('constructionAxes','ax_'),('constructionPoints','pt_')]:
            for entity in each(component,collection):name_check(entity,prefix)
        for feature in each(component,'features'):
            counts['features']+=1;name_check(feature);health(feature)
        for collection in ('joints','asBuiltJoints'):
            for joint in each(component,collection):
                counts['joints']+=1;name_check(joint);health(joint)
    for parameter in each(design,'userParameters'):
        counts['parameters']+=1
        name=read(parameter,'name')
        if name is not None and not re.fullmatch(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)*',name):
            finding('PARAMETER_NAME','review',parameter,'Prefer a readable snake_case user-parameter name.')
        comment=read(parameter,'comment')
        if comment is not None and not comment.strip():
            finding('PARAMETER_COMMENT','review',parameter,'Add an intent/limits comment.')
        favorite=read(parameter,'isFavorite')
        if favorite is False:
            finding('PARAMETER_FAVORITE','review',parameter,'Favorite this parameter if it is a driving user input.')
        dependents=each(parameter,'dependentParameters')
        if not dependents:
            finding('PARAMETER_USAGE','review',parameter,'No dependent parameter equations found. Review usage; this alone does not prove the parameter is unused. Do not auto-delete it.')
    errors=[f for f in findings if f['severity']=='error']
    reviews=[f for f in findings if f['severity']=='review']
    return {'rules_version':rules['rules_version'],'rules_sha256':rules['sha256'],
            'scope':'whole-design component definitions, including imported/linked definitions; occurrences are not duplicated',
            'counts':counts,'findings':findings,'unavailable_checks':unknown,
            'error_count':len(errors),'review_count':len(reviews),'inspection_complete':not unknown,
            'automated_checks_passed':not errors and not unknown,
            'full_standard_verified':False,'manual_review_required':MANUAL_REVIEW,
            'geometry_modified':False,'regeneration_performed':False}


def require(report,strict_reviews=False):
    if type(strict_reviews) is not bool:raise ValueError('strict_reviews must be boolean')
    if not report['automated_checks_passed'] or (strict_reviews and report['review_count']):
        raise RuntimeError('Modeling hygiene gate failed: %d errors, %d reviews, %d unavailable checks. Inspect recorded report; no export performed.' %
                           (report['error_count'],report['review_count'],len(report['unavailable_checks'])))
    return report
