"""Native parametric authoring helpers and an explicit parameter-only edit route."""
import re
import adsk.core
from . import advanced


def edit_parameters(ctx,changes):
    """Validate all edits before the first write. Native failures may leave partial edits."""
    if ctx.read_only or not ctx.boundary or not ctx.boundary.enabled:
        raise ValueError('Parameter-only edit requires a modeling task with explicit edit boundary')
    guard=ctx.authoring
    if not guard or not guard.record:
        raise ValueError('Parameter-only edit requires adopted task.authoring budget')
    if guard.policy['max_new_features']!=0 or guard.policy['max_new_sketches']!=0:
        raise ValueError('Parameter-only edit requires zero new-feature and new-sketch budgets')
    if not isinstance(changes,dict) or not 1<=len(changes)<=32:
        raise ValueError('Provide 1..32 existing named user-parameter expressions')
    prepared=[]
    for name,expression in changes.items():
        ctx.boundary.require_parameter(name)
        parameter=ctx.design.userParameters.itemByName(name)
        if not parameter or not isinstance(expression,str) or not expression.strip():
            raise ValueError('Existing user parameter and explicit expression required: '+str(name))
        if not ctx.design.unitsManager.isValidExpression(expression,parameter.unit):
            raise ValueError('Invalid expression or units: '+name)
        prepared.append((parameter,expression,parameter.expression))
    ctx.check_cancel()
    from .maintainability import counts
    before=counts(ctx.selection,guard.allowed)
    for parameter,expression,old in prepared:
        ctx.check_cancel()
        with ctx.operation('edit_existing_parameter',target={'parameter':parameter.name}):
            parameter.expression=expression
    ctx.synchronize()
    after=counts(ctx.selection,guard.allowed)
    if (before.keys()!=after.keys() or any(
            len(before[i][kind])!=len(after[i][kind]) or
            any(not any(e==old for old in before[i][kind]) for e in after[i][kind])
            for i in before for kind in ('features','sketches'))):
        raise RuntimeError('Parameter-only edit changed feature/sketch history; inspect partial result')
    if ctx.boundary.post().get('violations'):
        raise RuntimeError('Parameter-only edit violated protected scope; inspect partial result')
    return ctx.record('parameter_edit',{'route':'existing_user_parameters','changes':[
        {'name':p.name,'before':old,'after':p.expression} for p,expression,old in prepared],
        'history_preserved':True,'approval_status':'not_authenticated',
        'limitation':'Local parameter edit and history checks only; shape, junctions and appearance require separate evidence.'})

def circle(ctx,name,diameter_parameter):
    ctx.check_cancel();c=ctx.target;advanced.editable(ctx.design,c)
    if ctx.boundary:ctx.boundary.require_component(c)
    if not re.fullmatch(r'sk_[A-Za-z][A-Za-z0-9_]*',name):raise ValueError('Use sk_ purpose name')
    p=ctx.design.userParameters.itemByName(diameter_parameter)
    if not p or not ctx.design.unitsManager.isValidExpression(diameter_parameter,'mm'):
        raise ValueError('Create a named length parameter first')
    radius=ctx.design.unitsManager.evaluateExpression(diameter_parameter,'cm')/2
    if radius<=0:raise ValueError('Diameter must be positive')
    sketch=c.sketches.add(c.xYConstructionPlane);sketch.name=name
    # Start away from origin to avoid relying on inferred implicit coincident constraints.
    curve=sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(radius,radius,0),radius)
    sketch.geometricConstraints.addCoincident(curve.centerSketchPoint,sketch.originPoint)
    dim=sketch.sketchDimensions.addDiameterDimension(curve,adsk.core.Point3D.create(radius*2,0,0))
    if not dim:raise RuntimeError('Diameter dimension creation failed; inspect partial sketch')
    dim.parameter.expression=diameter_parameter
    ctx.synchronize()
    if not sketch.isFullyConstrained:raise RuntimeError('Native profile not fully constrained; inspect, do not silently rebuild')
    ctx.created(sketch)
    return sketch
