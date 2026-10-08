"""v0.2 topology, fillets and standard assembly joints. Loaded inside Fusion only."""
import math
import adsk.core
import adsk.fusion

OPS = {'capabilities', 'inspect_assembly', 'inspect_body', 'read_selection', 'fillet', 'joint'}

def each(c):
    return [c.item(i) for i in range(c.count)]

def native(e):
    return getattr(e, 'nativeObject', None) or e

def ref(e):
    result = {'token': native(e).entityToken, 'type': e.objectType}
    if hasattr(e, 'name'):
        result['name'] = e.name
    context = getattr(e, 'assemblyContext', None)
    result['occurrence_token'] = context.entityToken if context else ''
    return result

def point(p):
    return [p.x * 10, p.y * 10, p.z * 10]

def resolve(d, token, cls=None):
    matches = d.findEntityByToken(token)
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous entity. Inspect again before modifying.')
    e = matches[0]
    if cls:
        e = cls.cast(e)
    if not e:
        raise ValueError('Wrong entity type.')
    return e

def health(e):
    return dict(ref(e), health=str(e.healthState), message=e.errorOrWarningMessage)

def length(d, expression):
    if not d.unitsManager.isValidExpression(expression, 'mm'):
        raise ValueError('Invalid length expression.')
    value = d.unitsManager.evaluateExpression(expression, 'mm')
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Length must be finite and positive.')
    return adsk.core.ValueInput.createByString(expression)

def editable(d, component):
    for o in each(d.rootComponent.allOccurrences):
        if o.component == component and o.isReferencedComponent:
            raise ValueError('Linked component: edit its source document instead.')

def assembly(d):
    root = d.rootComponent
    occurrences = []
    for o in each(root.allOccurrences):
        occurrences.append({'name': o.name, 'path': o.fullPathName,
            'token': o.entityToken, 'component': ref(o.component),
            'grounded': o.isGrounded, 'linked': o.isReferencedComponent,
            'bodies': [ref(b) for b in each(o.component.bRepBodies)]})
    return {'version': '0.4.1', 'root_bodies': [ref(b) for b in each(root.bRepBodies)],
            'occurrences': occurrences,
            'joints': [health(j) for j in each(root.joints)],
            'as_built_joints': [health(j) for j in each(root.asBuiltJoints)]}

def geometry(d, token, occurrence_token, keypoint):
    e = native(resolve(d, token))
    owner = e.body.parentComponent if hasattr(e, 'body') else None
    if not owner:
        raise ValueError('Joint reference must be a BRep face, edge, or vertex.')
    if occurrence_token:
        occurrence = resolve(d, occurrence_token, adsk.fusion.Occurrence)
        if occurrence.component != owner:
            raise ValueError('Geometry does not belong to the selected occurrence.')
        e = e.createForAssemblyContext(occurrence)
    elif owner != d.rootComponent:
        raise ValueError('Component geometry requires its occurrence token.')
    keypoints = {'center': adsk.fusion.JointKeyPointTypes.CenterKeyPoint,
                 'start': adsk.fusion.JointKeyPointTypes.StartKeyPoint,
                 'end': adsk.fusion.JointKeyPointTypes.EndKeyPoint,
                 'middle': adsk.fusion.JointKeyPointTypes.MiddleKeyPoint}
    k = keypoints[keypoint]
    if adsk.fusion.BRepFace.cast(e):
        if not adsk.core.Plane.cast(e.geometry) or keypoint != 'center':
            raise ValueError('Face reference requires a planar face and center keypoint.')
        return adsk.fusion.JointGeometry.createByPlanarFace(e, None, k)
    if adsk.fusion.BRepEdge.cast(e):
        return adsk.fusion.JointGeometry.createByCurve(e, k)
    if adsk.fusion.BRepVertex.cast(e):
        return adsk.fusion.JointGeometry.createByPoint(e)
    raise ValueError('Unsupported joint reference.')

def execute(op, a, d, app):
    if op == 'capabilities':
        return {'version': '0.4.1', 'fillets': ['constant_radius'],
                'joints': ['rigid', 'revolute', 'slider', 'cylindrical'],
                'joint_mode': 'standard joints (can reposition components)',
                'batch_scripts': True, 'persistent_jobs': True, 'full_adsk_access': True,
                'full_assembly_inspection': True, 'geometry_selection': True, 'live_fusion_tested': False,
                'read_only_batches': True, 'explicit_root_target': '@root',
                'verified_motion_requires_expected_world': True, 'disposable_experiments': True,
                'tolerance_budgets': True, 'semantic_selectors': True,
                'surface_review_candidates': True, 'full_print_audit': False,
                'release_hash_revision_checks': True, 'modeling_hygiene_audit': True,
                'checked_export_gate': True, 'modeling_rules_version': '1.0.3'}
    if op == 'inspect_assembly':
        return assembly(d)
    if op == 'read_selection':
        result = []
        for s in each(app.userInterface.activeSelections):
            try:
                result.append(ref(s.entity))
            except AttributeError:
                result.append({'type': s.entity.objectType, 'unsupported': True})
        return {'selection': result}
    if op == 'inspect_body':
        b = native(resolve(d, a['body_token'], adsk.fusion.BRepBody))
        edges = []
        for e in each(b.edges):
            edges.append(dict(ref(e), length_mm=e.length * 10,
                curve_type=e.geometry.objectType,
                start_mm=point(e.startVertex.geometry) if e.startVertex else None,
                end_mm=point(e.endVertex.geometry) if e.endVertex else None,
                point_on_edge_mm=point(e.pointOnEdge)))
        faces = [dict(ref(f), surface_type=f.geometry.objectType,
                      point_on_face_mm=point(f.pointOnFace),
                      area_mm2=f.area * 100,
                      edges=[native(e).entityToken for e in each(f.edges)]) for f in each(b.faces)]
        return {'body': ref(b), 'component': ref(b.parentComponent),
                'coordinate_system': 'component-local millimetres', 'edges': edges, 'faces': faces,
                'vertices': [dict(ref(v), position_mm=point(v.geometry)) for v in each(b.vertices)]}
    if op == 'fillet':
        radius = length(d, a['radius'])
        if not a['edge_tokens'] or len(a['edge_tokens']) > 500:
            raise ValueError('Select 1 to 500 edges.')
        edges = [native(resolve(d, t, adsk.fusion.BRepEdge)) for t in a['edge_tokens']]
        body = edges[0].body
        if any(e.body != body for e in edges):
            raise ValueError('Fillet edges must belong to one body.')
        editable(d, body.parentComponent)
        collection = adsk.core.ObjectCollection.create()
        for e in edges:
            if not collection.contains(e):
                collection.add(e)
        features = body.parentComponent.features.filletFeatures
        inp = features.createInput()
        inp.isRollingBallCorner = a['rolling_ball']
        inp.edgeSetInputs.addConstantRadiusEdgeSet(collection, radius, a['tangent_chain'])
        feature = features.add(inp)
        feature.name = a['name']
        return health(feature)
    if op == 'joint':
        t1, t2 = a['occurrence_one'], a['occurrence_two']
        # Resolve occurrences and compare actual objects, not token strings.
        o1 = resolve(d, t1, adsk.fusion.Occurrence) if t1 else None
        o2 = resolve(d, t2, adsk.fusion.Occurrence) if t2 else None
        if o1 == o2:
            raise ValueError('Joint must connect different occurrences, or occurrence and root.')
        if o1 and o2:
            p1, p2 = o1.fullPathName, o2.fullPathName
            if p1.startswith(p2 + '+') or p2.startswith(p1 + '+'):
                raise ValueError('Cannot joint an occurrence to its own ancestor.')
        g1 = geometry(d, a['geometry_one'], t1, a['keypoint_one'])
        g2 = geometry(d, a['geometry_two'], t2, a['keypoint_two'])
        for expr, unit in ((a['offset'], 'mm'), (a['angle'], 'deg')):
            if not d.unitsManager.isValidExpression(expr, unit):
                raise ValueError('Invalid joint offset or angle expression.')
        joints = d.rootComponent.joints
        inp = joints.createInput(g1, g2)
        inp.offset = adsk.core.ValueInput.createByString(a['offset'])
        inp.angle = adsk.core.ValueInput.createByString(a['angle'])
        inp.isFlipped = a['flipped']
        direction = getattr(adsk.fusion.JointDirections, a['axis'] + 'AxisJointDirection')
        kind = a['kind']
        if kind == 'rigid':
            ok = inp.setAsRigidJointMotion()
        elif kind == 'revolute':
            ok = inp.setAsRevoluteJointMotion(direction)
        elif kind == 'slider':
            ok = inp.setAsSliderJointMotion(direction)
        elif kind == 'cylindrical':
            ok = inp.setAsCylindricalJointMotion(direction)
        else:
            raise ValueError('Unsupported joint kind.')
        if not ok:
            raise ValueError('Fusion rejected the joint motion definition.')
        joint = joints.add(inp)
        joint.name = a['name']
        return health(joint)
    raise ValueError('Unknown advanced operation.')
