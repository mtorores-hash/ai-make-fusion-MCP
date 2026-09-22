# Script Api

## Script contract

```python
def run(ctx):
    import adsk.core
    import adsk.fusion
    ctx.stage('build mechanism', 0.10)   # checkpoint before this major stage
    component = ctx.target
    # Use the full adsk API here: sketches, constraints, planes, features, assemblies.
    ctx.record('design_intent', {'insert_diameter_mm': 12})
    ctx.progress(0.80, 'Checking geometry')
    ctx.record('health', ctx.validate())
    ctx.export('mechanism.f3d', ctx.design.rootComponent)
    ctx.capture('mechanism.png', 1920, 1080)
    return {'summary': 'Model and validation complete'}
```

`run(ctx)` is synchronous and must return JSON-serializable data (or None). `adsk`, `app`,
`design`, `target`, `ctx` are also available in module scope. Keep modeling inside run.
All script code runs on Fusion's main thread through the custom-event handler. API
operations are serialized; the handler rejects reentrant execution. Worker threads only
monitor files/jobs and fire the custom event. Job polling reads SQLite independently.

**Execution boundary:** this is trusted, unrestricted Python, running with your OS/Fusion
permissions. It is not a sandbox. Document/component checks catch targeting mistakes
before execution and at cooperative boundaries; arbitrary script code can bypass that
intent by directly using other documents or filesystem/network APIs. Use it for scripts
Codex creates for your authorized design tasks. Do not submit unreviewed external code.

Declared units apply to `ctx.point` and numeric `ctx.value`. Raw `adsk` geometry floats
still use Fusion internal **centimetres and radians**, regardless of document display units.
String expressions should include explicit units or refer to named parameters.

Long scripts can keep Fusion's UI busy. Call `ctx.progress`, `ctx.stage` or `ctx.check_cancel`
between meaningful steps. Cancellation cannot interrupt an in-progress kernel call or a
Python infinite loop. There is no forced timeout, automatic rollback or automatic resume.
Avoid `adsk.doEvents()` loops and never call Fusion APIs from script-created threads.

## Helpers exposed as ctx methods

| Helper | Behavior |
| --- | --- |
| `point(x,y,z=0)` / `value(expression)` | Explicit unit conversion / Fusion ValueInput |
| `parameter(name,expression,unit=None)` | Create/update named user parameter |
| `progress(fraction,message)` | Persist progress, check target/cancellation |
| `stage(label,fraction,checkpoint=True)` | Progress plus pre-stage native archive |
| `checkpoint(label)` | Full-design F3D archive; fail visibly if export is unavailable |
| `created(entity)` / `ref(entity)` | Register or obtain native references with occurrence context |
| `record(name,value)` / `warn(message)` | Structured measurements / warnings |
| `inspect(include_topology=False)` | All components, nested occurrences, health, dimensions, transforms |
| `resolve(reference,world=False)` | Resolve `{token, occurrence_token}` to native/proxy geometry |
| `select_edges(body,filters,feature=None)` | Geometric predicates plus optional current feature boundary |
| `select_faces(body,filters,feature=None)` | Surface predicates plus optional current feature faces |
| `expect_one(matches)` | Reject zero/ambiguous selections |
| `validate()` | Feature/joint health across components |
| `minimum_distance(one,two)` | World-space minimum distance in mm |
| `interference(references)` | Current-pose interference results and volumes in mm³ |
| `section_sketch(body,plane,offset,name)` | Body/plane intersection curves in an editable sketch |
| `import_step(absolute_path)` | Import real hardware into target component |
| `set_joint_limits(joint,min,max,motion,unit)` | Rotation or slide limits with explicit unit conversion |
| `sample_motion(joint,positions,pairs,motion,unit,capture)` | Pose samples, pair checks and optional PNG frames; restore starting pose |
| `export(filename,entity=None)` | Editable F3D, STEP/STP or STL; defaults to target component |
| `export_print_copy(body,Matrix3D,stem)` | Orient a temporary copy, export STL/STEP, remove copy |
| `camera(eye,target,up,fit)` | Set view; eye/target use declared units in world coordinates |
| `capture(filename,width,height)` | PNG capture; verify actual header dimensions, default 1920×1080 |
| `apply_appearance(entity,appearance)` | Copy/assign a Fusion Appearance object |
| `color(entity,name,rgb,base_appearance)` | White/blue or other RGB using a compatible generic_diffuse material |
| `path(filename)` / `artifact(path)` | Unique job output path / register file with size and SHA-256 |

The full `adsk` API is available for operations without convenience wrappers: constrained
lines/arcs/splines, projections, extrude-to-face and participant-body selection, revolve,
sweep, loft, chamfer, mirror, pattern, split, component transforms and other joint types.
Those operations require correct Fusion API code in the batch; this is not a separate
validated wrapper for every operation. Scripts should use named sketch dimensions, not
just create unused user parameters.

Section helpers create **section curves**, not an interactive clipped-solid Section
Analysis display. Rendered frames are exported PNGs, not an encoded animation video.
F3D archives retain editable native design data; STEP/STL do not retain the feature timeline.
Linked/external-reference designs may reject F3D checkpoints: the batch then fails BEFORE
executing the script. Use an appropriate editable local source design; do not silently
skip a failed checkpoint. Cloud project save/version management is not automated here.

