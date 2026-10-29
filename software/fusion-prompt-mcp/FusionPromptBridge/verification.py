"""Numerical verification policies; no Autodesk imports, no implicit certification."""
import hashlib
import json
import math
from pathlib import Path


def finite(value, name='value', nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(name + ' must be a finite number')
    if nonnegative and value < 0:
        raise ValueError(name + ' must be nonnegative')
    return float(value)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def clearance_budget(name, nominal_mm, terms, kind='axial', allowance_mm=0):
    """Signed independent bounds on clearance contributions, all in mm.

    Each term: name, lower_mm, upper_mm, provenance, status. Bounds are deviations
    from nominal clearance, NOT raw part sizes. Do not mix radial and diametral terms.
    """
    if kind not in ('axial', 'radial', 'diametral'):
        raise ValueError('kind must be axial, radial or diametral')
    nominal = finite(nominal_mm); allowance = finite(allowance_mm, 'allowance_mm', True)
    if not name or not terms:
        raise ValueError('Named interface and explicit uncertainty terms required')
    rows = []; names = set()
    for term in terms:
        if not term.get('name') or term['name'] in names:
            raise ValueError('Each term requires a unique name')
        names.add(term['name'])
        low = finite(term['lower_mm']); high = finite(term['upper_mm'])
        if low > 0 or high < 0 or low > high:
            raise ValueError('Deviation bounds must contain zero')
        if not term.get('provenance') or term.get('status') not in ('measured', 'specified', 'provisional'):
            raise ValueError('Each term requires provenance and measured/specified/provisional status')
        rows.append(dict(term, lower_mm=low, upper_mm=high))
    worst = nominal + sum(t['lower_mm'] for t in rows) - allowance
    return {'name': name, 'kind': kind, 'nominal_clearance_mm': nominal,
            'allowance_mm': allowance, 'nominal_margin_mm': nominal-allowance,
            'worst_case_margin_mm': worst,
            'best_case_margin_mm': nominal+sum(t['upper_mm'] for t in rows)-allowance,
            'passes_bounds': worst >= 0, 'provisional': any(t['status']=='provisional' for t in rows),
            'controlling_terms': sorted(rows, key=lambda t:t['lower_mm']),
            'limitation': 'Independent signed dimensional bounds only; angular, backlash and load effects must be supplied as separate justified terms. Not a fit certification.'}


def geometry_delta(before, after, rules):
    """Compare measured snapshots. Mandatory guards prevent an empty acceptance policy."""
    required = {'expected_body_count', 'max_volume_change_mm3', 'max_envelope_change_mm'}
    if required - rules.keys():
        raise ValueError('Missing acceptance rules: '+str(sorted(required-rules.keys())))
    count = rules['expected_body_count']
    if type(count) is not int or count < 1:
        raise ValueError('expected_body_count must be a positive integer')
    vlimit = finite(rules['max_volume_change_mm3'], 'volume limit', True)
    elimit = finite(rules['max_envelope_change_mm'], 'envelope limit', True)
    reasons = []
    if after['body_count'] != count: reasons.append('body_count')
    if not after['all_solid'] or not after['all_valid']: reasons.append('solid_validity')
    delta = after['volume_mm3']-before['volume_mm3']
    finite(delta, 'volume delta')
    if abs(delta) > vlimit: reasons.append('volume_change')
    if len(before['envelope_mm']) != 6 or len(after['envelope_mm']) != 6:
        raise ValueError('Envelope must contain six bounds')
    envelope = [finite(b)-finite(a) for a,b in zip(before['envelope_mm'],after['envelope_mm'])]
    if max(map(abs,envelope)) > elimit: reasons.append('envelope_change')
    if after['feature_errors'] or after.get('inspection_warnings'): reasons.append('feature_health_or_incomplete_inspection')
    # Protected metrics are independently remeasured by the caller on each document.
    for name, tolerance in rules.get('protected_metrics', {}).items():
        tolerance = finite(tolerance, 'protected tolerance', True)
        if name not in before.get('protected', {}) or name not in after.get('protected', {}):
            reasons.append('missing_protected:'+name); continue
        if abs(finite(after['protected'][name])-finite(before['protected'][name])) > tolerance:
            reasons.append('protected:'+name)
    return {'accepted': not reasons, 'reasons': reasons, 'volume_change_mm3':delta,
            'envelope_change_mm':envelope, 'before':before, 'after':after, 'rules':rules}


def separated_boxes(a, b, padding_mm=0):
    """Conservative AABB rejection. Inputs MUST share a coordinate frame."""
    padding = finite(padding_mm, 'padding_mm', True)
    for box in (a,b):
        if len(box['min_mm']) != 3 or len(box['max_mm']) != 3:
            raise ValueError('AABB needs three coordinates')
        for low, high in zip(box['min_mm'],box['max_mm']):
            if finite(low) > finite(high): raise ValueError('Invalid AABB')
    return any(a['max_mm'][i]+padding < b['min_mm'][i] or
               b['max_mm'][i]+padding < a['min_mm'][i] for i in range(3))


def matrix_error(actual, expected):
    if len(actual)!=16 or len(expected)!=16:
        raise ValueError('Transforms must have 16 row-major entries')
    for value in list(actual)+list(expected): finite(value, 'transform entry')
    # Fusion matrix translations use cm; rotations are dimensionless.
    return {'translation_mm':math.sqrt(sum((actual[i]-expected[i])**2 for i in (3,7,11)))*10,
            'rotation_entry_max':max(abs(actual[i]-expected[i]) for i in (0,1,2,4,5,6,8,9,10)),
            'homogeneous_entry_max':max(abs(actual[i]-expected[i]) for i in (12,13,14,15))}


def adaptive_samples(positions, evaluate, near_contact_mm, max_depth=4, max_samples=1000):
    """Midpoint subdivision of every interval, then extra near-contact refinement.

    Every final interval remains unresolved for continuous collision proof. This is
    intentional: no finite point sampler can exclude an arbitrarily narrow collision.
    """
    threshold=finite(near_contact_mm, 'near_contact_mm', True)
    if type(max_depth) is not int or not 0<=max_depth<=12: raise ValueError('max_depth must be 0..12')
    if type(max_samples) is not int or not 2<=max_samples<=10000: raise ValueError('max_samples must be 2..10000')
    xs=sorted(set(finite(x,'position') for x in positions))
    if len(xs)<2 or len(xs)>max_samples: raise ValueError('Provide 2..max_samples distinct positions')
    rows={}; intervals=[]
    def sample(x):
        if x not in rows:
            row=evaluate(x)
            if 'clearance_mm' not in row or 'collision' not in row: raise ValueError('Evaluator needs clearance_mm and collision')
            finite(row['clearance_mm'], 'clearance_mm', True)
            if type(row['collision']) is not bool: raise ValueError('collision must be boolean')
            rows[x]=dict(row,position=x)
        return rows[x]
    for x in xs: sample(x)
    def refine(a,b,depth):
        # Always split once (even clear endpoints); further splits use contact proximity.
        near=min(rows[a]['clearance_mm'],rows[b]['clearance_mm'])<=threshold or rows[a]['collision'] or rows[b]['collision']
        if depth>=max_depth or (depth>0 and not near) or len(rows)>=max_samples:
            intervals.append({'start':a,'end':b,'depth':depth,
                              'reason':'sample_budget' if len(rows)>=max_samples else 'finite_sampling'})
            return
        mid=(a+b)/2
        sample(mid); refine(a,mid,depth+1); refine(mid,b,depth+1)
    for a,b in zip(xs,xs[1:]): refine(a,b,0)
    return {'samples':[rows[x] for x in sorted(rows)], 'unresolved_intervals':intervals,
            'continuous_collision_proof':False, 'sample_count':len(rows),
            'limitation':'May miss collisions between poses, including narrow intervals away from sampled contact.'}


def file_hash(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): digest.update(block)
    return digest.hexdigest()


def build_manifest(model_revision, entries, checks):
    """Entries carry a revision from generation time; never infer it from current files."""
    if not model_revision or not entries or not checks: raise ValueError('Revision, artifacts and checks required')
    artifacts=[]; paths=set()
    for entry in entries:
        path=Path(entry['path']).resolve()
        if path in paths: raise ValueError('Duplicate artifact path')
        paths.add(path)
        if entry['model_revision']!=model_revision: raise ValueError('Stale artifact: '+str(path))
        # Require a generation-time digest to reject overwritten files.
        digest=file_hash(path)
        if entry.get('sha256')!=digest: raise ValueError('Artifact hash changed: '+str(path))
        artifacts.append(dict(entry,path=str(path),bytes=path.stat().st_size))
    for check in checks:
        if check.get('model_revision')!=model_revision: raise ValueError('Stale check')
        if check.get('passed') is not True or not check.get('name'):
            raise ValueError('Every release check must be named and passed')
        if check.get('evidence') not in ('measured','calculated','observed'):
            raise ValueError('Release check requires evidence classification')
    return {'schema':1,'model_revision':model_revision,'artifacts':artifacts,'checks':checks,
            'scope':'Provenance and byte consistency only. Geometry, round-trip and manufacturing checks must be supplied explicitly.'}


def validate_manifest(manifest, current_revision):
    if manifest['model_revision']!=current_revision: raise ValueError('Manifest is stale for this model')
    return build_manifest(current_revision,manifest['artifacts'],manifest['checks'])
