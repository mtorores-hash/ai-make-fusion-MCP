"""Batch acceptance example, not a BRANCA production design.
Set units='mm'; explicitly target an empty local component (root works too).
Create an annular spring cup whose insert diameter and wall update through named dimensions.
"""
def run(ctx):
    import adsk.core
    import adsk.fusion
    c=ctx.target
    ctx.stage('parameters_and_sketch',0.05,checkpoint=False)  # Initial automatic checkpoint already exists.
    ctx.parameter('branca_insert_diameter','12 mm')
    ctx.parameter('branca_cup_wall','2 mm')
    ctx.parameter('branca_cup_height','10 mm')
    ctx.parameter('branca_outer_diameter','branca_insert_diameter + 2 * branca_cup_wall')
    sketch=ctx.created(c.sketches.add(c.xYConstructionPlane)); sketch.name='BRANCA Spring Cup Profile'
    circles=sketch.sketchCurves.sketchCircles
    inner=circles.addByCenterRadius(ctx.point(2,3),0.6)
    outer=circles.addByCenterRadius(ctx.point(4,5),0.8)
    # Constrain centers to origin; dimensional constraints drive actual geometry.
    sketch.geometricConstraints.addCoincident(inner.centerSketchPoint,sketch.originPoint)
    sketch.geometricConstraints.addCoincident(outer.centerSketchPoint,sketch.originPoint)
    dim1=sketch.sketchDimensions.addDiameterDimension(inner,ctx.point(16,0))
    dim1.parameter.expression='branca_insert_diameter'
    dim2=sketch.sketchDimensions.addDiameterDimension(outer,ctx.point(20,5))
    dim2.parameter.expression='branca_outer_diameter'
    # Choose the annulus by profile topology instead of assuming profile index.
    profiles=[sketch.profiles.item(i) for i in range(sketch.profiles.count)
              if sketch.profiles.item(i).profileLoops.count==2]
    profile=ctx.expect_one(profiles)
    ctx.stage('extrude',0.30)
    feature=ctx.created(c.features.extrudeFeatures.addSimple(profile,ctx.value('branca_cup_height'),
                           adsk.fusion.FeatureOperations.NewBodyFeatureOperation))
    feature.name='Spring Cup Wall'; body=ctx.created(feature.bodies.item(0)); body.name='Spring Cup'
    ctx.stage('parameter_update_check',0.55)
    p=ctx.design.userParameters.itemByName('branca_insert_diameter'); original=p.expression
    initial_volume=body.volume*1000
    try:
        p.expression='14 mm'
        if not ctx.design.computeAll(): raise RuntimeError('Parameter edit did not recompute.')
        changed_volume=body.volume*1000
        if abs(changed_volume-initial_volume)<0.001: raise RuntimeError('Geometry did not respond to parameter.')
    finally:
        p.expression=original
        if not ctx.design.computeAll(): raise RuntimeError('Parameter restoration failed.')
    ctx.record('parametric_check',{'before_mm3':initial_volume,'edited_mm3':changed_volume,
                                  'restored_expression':original})
    # Geometric selector: top circular edges of this feature (not edge numbers).
    edges=ctx.select_edges(body,{'geometry_type':'Circle3D','at_coordinate_mm':{'z':10}},feature)
    ctx.record('top_edge_candidates',[ctx.ref(e) for e in edges])
    ctx.record('sketch_fully_constrained',sketch.isFullyConstrained)
    ctx.progress(0.85,'Export and presentation')
    ctx.export('spring_cup.f3d',c); ctx.export('spring_cup.step',c); ctx.export('spring_cup.stl',body)
    ctx.camera((45,45,35),(0,0,5),fit=True); ctx.capture('spring_cup_1920x1080.png')
    ctx.record('health',ctx.validate())
    return {'part':'spring cup','note':'Annular example; does not include a base, tabs or BRANCA-specific fit geometry.'}
