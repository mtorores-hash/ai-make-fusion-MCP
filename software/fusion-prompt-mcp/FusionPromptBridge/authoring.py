"""Reusable native, component-owned circular profile with a driving named parameter."""
import re
import adsk.core
from . import advanced

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
