# MCP tool reference — v0.4.0

Signatures generated from server.py. Local STDIO; see [installation](installation.md).

## `inspect_design`

```python
inspect_design()
```

Read active design ID, root bodies, sketches, parameters, and feature health.

## `new_design`

```python
new_design()
```

Open a new unsaved parametric design without closing existing documents.

## `rectangle_sketch`

```python
rectangle_sketch(design_id: str, name: str, width_mm: float, height_mm: float, x_mm: float=0, y_mm: float=0, plane: Literal['XY', 'XZ', 'YZ']='XY')
```

Create a rectangle in a new root sketch from a lower-left corner. Size is initial geometry,
not driven by named parameters. Returns a sketch token for extrude.

## `circle_sketch`

```python
circle_sketch(design_id: str, name: str, diameter_mm: float, x_mm: float=0, y_mm: float=0, plane: Literal['XY', 'XZ', 'YZ']='XY')
```

Create a circle in a new root sketch. Coordinates are sketch-local mm.

## `extrude`

```python
extrude(design_id: str, sketch_token: str, distance: str, name: str, operation: Literal['new_body', 'new_component', 'join', 'cut']='new_body', profile_index: int=0, target_body_token: str='')
```

Extrude a profile; distance is positive, e.g. '4 mm' or 'plate_thickness'.
new_component creates an assembly component. Cut requires target_body_token. Starts at sketch plane in positive normal direction.
Join may affect touching root bodies. Inspect before and after.

## `set_parameter`

```python
set_parameter(design_id: str, name: str, expression: str, unit: str='mm')
```

Create/update a user parameter. Existing model parameters can also be updated by name.
Example expression '4 mm'. Only features that reference it will change.

## `export_model`

```python
export_model(design_id: str, filename: str, format: Literal['step', 'stl'], body_token: str='')
```

Export STEP of root component or STL of one specified body. Filename only, no paths.
Writes to ~/FusionPromptExports and refuses overwrites. Returns local path.

## `fusion_capabilities`

```python
fusion_capabilities(design_id: str)
```

Report loaded add-in version and supported advanced operations.

## `inspect_assembly`

```python
inspect_assembly(design_id: str)
```

List native components, occurrence tokens, component body tokens and root joints.
Keep the occurrence token with native geometry to distinguish repeated instances.

## `inspect_body`

```python
inspect_body(design_id: str, body_token: str)
```

List edge/face/vertex tokens and component-local geometry in mm.
Reinspect after topology edits; do not guess edge indices.

## `read_selection`

```python
read_selection(design_id: str)
```

Read entities selected by the user in Fusion, with occurrence contexts.
Useful when verbal edge/face descriptions are ambiguous. Finish active commands first.

## `fillet_edges`

```python
fillet_edges(design_id: str, edge_tokens: list[str], radius: str, name: str='MCP Fillet', tangent_chain: bool=False, rolling_ball: bool=True)
```

Create a native constant-radius fillet on explicitly inspected/selected edges of one body.
Radius accepts '2 mm' or a parameter. Works inside local components; modifying a component
definition affects ALL its instances. Linked components must be edited in their source.
Kernel failures can occur for oversized radii. Inspect health and topology after editing.

## `create_joint`

```python
create_joint(design_id: str, geometry_one: str, geometry_two: str, occurrence_one: str='', occurrence_two: str='', kind: Literal['rigid', 'revolute', 'slider', 'cylindrical']='rigid', name: str='MCP Joint', axis: Literal['X', 'Y', 'Z']='Z', keypoint_one: Literal['center', 'start', 'end', 'middle']='center', keypoint_two: Literal['center', 'start', 'end', 'middle']='center', offset: str='0 mm', angle: str='0 deg', flipped: bool=False)
```

Create a STANDARD joint: Fusion may reposition components to align the references.
Use planar face centers, compatible edge keypoints, or vertices from inspect_body/selection.
Each component reference needs its occurrence token from inspect_assembly; empty means root.
Axis is in the joint frame, NOT global coordinates. This is not an as-built joint.
Preserve existing placements unless the user requested alignment. Inspect returned health.

## `run_model_script`

```python
run_model_script(operation_id: str, document_id: str, component_token: str, units: Literal['mm', 'cm', 'm', 'in'], script: str, checkpoint_before: bool=True, validate_after: bool=True, mode: Literal['modeling', 'read_only']='modeling')
```

Enqueue a complete trusted Fusion Python script defining run(ctx); returns immediately.
Arbitrary Python executes with the user's permissions INSIDE Fusion, on its main thread.
document_id is inspect_design.design_id; component_token is an explicit Component token or @root.
mode=read_only accepts ONLY def run(ctx): return queries with literal arguments to
ctx.inspect/validate/minimum_distance/interference/capture. Set checkpoint_before=False.
Read-only queries do not regenerate. Full Python modeling always regenerates at completion.
Use ctx.target, ctx.point/value, ctx.progress, ctx.stage, ctx.record, ctx.export and return JSON.
The same operation_id + exact request returns the same job; changed content is rejected.
Poll job_status/job_result; NEVER auto-retry an interrupted job with a fresh ID.
Checkpoints export the full design before code runs. Failure aborts before modeling.
Cancellation is cooperative; a kernel call or tight Python loop cannot be forcibly interrupted.
Units declare helper inputs; raw adsk floats STILL use Fusion native cm/radians.

## `job_status`

```python
job_status(job_id: str)
```

Read durable status/progress without waiting for Fusion's UI thread.

## `job_result`

```python
job_result(job_id: str)
```

Read structured results, created refs, measurements, warnings, files and full traceback.
While running, returns the latest flushed partial result. Local file paths refer to Fusion's PC.

## `list_jobs`

```python
list_jobs(limit: int=30)
```

Find previous jobs after reconnecting; newest first.

## `cancel_job`

```python
cancel_job(job_id: str)
```

Cancel queued work, or request cooperative cancellation of running work. No automatic rollback.

## `inspect_full_assembly`

```python
inspect_full_assembly(design_id: str, include_topology: bool=False, offset: int=0, limit: int=10)
```

Page all component definitions including nested bodies, feature/joint health, sketch dimensions,
named parameters and occurrence transforms. Optional faces/edges can be large. Follow next_offset.
Geometry is component-local mm; transform matrices use cm. ctx.inspect(True) returns all pages in a batch.

## `select_geometry`

```python
select_geometry(design_id: str, body_token: str, kind: Literal['edge', 'face'], filters: dict, feature_token: str='')
```

Select ALL matches by geometry, optionally bounded by current faces of an originating feature.
Filters: geometry_type (Line3D/Plane/Cylinder/Circle3D), parallel_to or normal_parallel_to [x,y,z],
length_mm/radius_mm/area_mm2 [min,max], within_box_mm [[minxyz],[maxxyz]],
at_coordinate_mm {x:...,y:...,z:...}, tolerance_mm, angular_tolerance_deg.
Bounds and directions are COMPONENT-LOCAL. Requery after edits; check count, never blindly use first.
Feature association means its CURRENT faces/boundary edges, not immutable historical provenance.

## `measure_minimum_distance`

```python
measure_minimum_distance(design_id: str, one: dict, two: dict)
```

World-space minimum distance in mm. Refs: {token, occurrence_token}.
Component geometry needs occurrence context. Zero may mean touching or overlapping.

## `check_interference`

```python
check_interference(design_id: str, references: list[dict])
```

Check current-pose interference volumes for body/occurrence references in assembly context.
Preserves design type. API unsupported-state errors are reported, never treated as a clear result.

## `validate_model`

```python
validate_model(design_id: str)
```

Report feature/joint errors and warnings across component definitions. Not a printability guarantee.
