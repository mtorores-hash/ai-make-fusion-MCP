> v0.5.0 adds installed modeling rules, `get_modeling_rules`, `audit_modeling_hygiene`,
> the `fusion://modeling-rules` resource and explicit `ctx.export_checked`. Copy the entire
> folder, including `modeling-rules.md`. See `../../docs/modeling-hygiene.md`.

> v0.4 development update: read `../../docs/upgrade-v0.4.md` and
> `../../docs/installation.md` in the repository for current behavior and migration.
> `sample_motion` now requires independent expected_world(position) transforms.
> The v0.3 instructions below describe the baseline; the v0.4 update supersedes conflicts.

# Fusion Prompt MCP v0.3 — persistent batch modeling

Give Codex a design task. Codex can now submit one complete Fusion Python script to build,
inspect and export a model, instead of issuing hundreds of single-feature MCP calls.
The 13 previous tools remain, with 10 new tools for batch jobs and validation.

**Status:** 40 automated tests pass using real SQLite/filesystem operations and Fusion API
test doubles. Real MCP initialization, all 23 tool schemas, enqueue/status, duplicate
rejection and queued cancellation pass. Python syntax checks pass. No Autodesk Fusion
installation is available in the build environment. CAD geometry, Windows add-in loading,
checkpoint/export behavior, nested transforms and joint solving still need live acceptance.
This package is not a validated mechanical design.

## Upgrade from v0.1 or v0.2

1. Save your Fusion document and stop FusionPromptBridge in Scripts and Add-Ins.
2. Back up the existing installation folder outside itself.
3. Extract this ZIP. Copy the contents of its `fusion-prompt-mcp` folder into the existing
   installation, replacing matching supplied files. Copy the ENTIRE `FusionPromptBridge`
   folder: `job_store.py`, `batch_runner.py` and `model_tools.py` are required.
   Keep `.venv` and your existing MCP configuration. Do not move the installation.
4. Restart Fusion to clear imported Python modules, then run FusionPromptBridge.
5. Restart the Fusion MCP connection in your desktop client.
6. Ask Codex to inspect the active design and call fusion_capabilities. It should report
   **0.3.0**, `batch_scripts: true`, and expose `run_model_script` plus `job_status`.

These steps update your PC; the hosted development session has not modified that PC.

## Fresh Windows installation

Extract to `C:\AI-Make\fusion-prompt-mcp`. Install Python 3.10+ and run in PowerShell:

```powershell
cd C:\AI-Make\fusion-prompt-mcp
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

In Fusion's Scripts and Add-Ins dialog add the existing `FusionPromptBridge` folder and
run it. In your desktop client's local STDIO MCP settings use:

- Command: `C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe`
- One argument: `C:\AI-Make\fusion-prompt-mcp\server.py`

Equivalent Codex config entry (merge with existing config, do not replace it):

```toml
[mcp_servers.fusion]
command = 'C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe'
args = ['C:\AI-Make\fusion-prompt-mcp\server.py']
tool_timeout_sec = 45
```

Both processes run natively on the Fusion PC under the same OS account. Only one Fusion
instance can own the bridge; an OS lock enforces this. Hosted browser/mobile chats and
WSL/container environments do not share this local connection automatically.

## Batch workflow

1. `inspect_design` returns `design_id` and `root_component.token`.
2. `inspect_assembly` / `inspect_full_assembly` identifies another component if desired.
   Select an explicit **Component** token, not an occurrence token, for modeling scope.
3. `run_model_script` accepts operation_id, document_id, component_token, units, script,
   checkpoint_before (default true) and validate_after (default true).
4. Submission durably stores the request and returns a job_id immediately.
5. Poll `job_status(job_id)`; call `job_result(job_id)` for partial/final structured results.
   The MCP connection can close without stopping a submitted job.
6. `list_jobs` recovers IDs after reconnecting; `cancel_job` cancels queued jobs or requests
   cooperative cancellation from a running script.

States: queued → waiting (if a Fusion command is active) → running → succeeded / failed /
cancelled. Restart recovery marks previously running jobs **interrupted**; it never replays
those jobs. A queued job retains its original document target and is rejected if it no
longer matches. Document IDs are bridge-session IDs, not persistent cloud document IDs.
Reinspect after an add-in restart before submitting new work.

The **same operation_id and identical complete request** returns the same job at any
status. Different content with the same ID fails. After an uncertain outcome, do not invent
a new ID and replay the script: inspect the job, model and checkpoints first.

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

## Geometric selection

The selector returns ALL matches with a count. It never silently chooses the first edge.
Example: restrict to vertical line edges in a tower's local bounding region, associated
with the current faces of its extrusion:

```python
edges = ctx.select_edges(tower_body, {
    'geometry_type': 'Line3D',
    'parallel_to': [0, 0, 1],
    'length_mm': [20, 40],
    'within_box_mm': [[-8, -8, 0], [8, 8, 45]],
    'tolerance_mm': 0.05
}, feature=tower_extrusion)
ctx.record('tower_edge_candidates', [ctx.ref(e) for e in edges])
```

Supported predicates: geometry_type; parallel_to; normal_parallel_to; length_mm,
radius_mm and area_mm2 ranges; within_box_mm; at_coordinate_mm; tolerance_mm;
angular_tolerance_deg. Geometry is component-local. Geometric bounds describe whole
entities, so `at_coordinate_mm: {'z': 10}` selects geometry entirely on that plane.

“Outer spring-tower edges” remains a design-intent interpretation Codex must translate
using the inspected model. Feature filtering uses its current faces/boundary edges, not
immutable historical topology. Requery after an edit; compare live entities when needed,
not entityToken string equality. Existing read_selection remains available for ambiguous
cases. Repeated instances require occurrence context for assembly checks.

## Results, checkpoints and recovery

Jobs live in `%USERPROFILE%\.fusion-prompt-mcp\jobs.sqlite3`. Files are under
`%USERPROFILE%\.fusion-prompt-mcp\artifacts\<job_id>\`. These are on your Fusion PC.
Do not place this directory on a shared/network drive or delete it while jobs run.

Results contain explicit `created` references, automatically detected new components,
bodies, sketches, features/joints in `created_detected`, measurements, warnings, files,
checkpoints, validation, return_value, stdout and full traceback. Progress flushes partial
results. stdout is limited to 1,000,000 characters; error tracebacks are not truncated.
Generated files must use the helpers or be registered with ctx.artifact to appear in the
result manifest. File paths are returned, not uploaded to a remote chat automatically.

The default checkpoint is before ANY submitted module code runs. `ctx.stage` adds explicit
checkpoints before major changes. There is no automatic identification of stage boundaries
inside arbitrary Python. Failure/cancellation can leave partial geometry changes. Restore
by opening the last usable F3D checkpoint as a separate design and inspecting it; automatic
restore could overwrite unrelated work, so it is intentionally not performed.

Submission idempotency prevents accidental repeated execution under normal operation.
It is not an atomic transaction across Fusion's model and SQLite: a crash can happen after
geometry changes and before the success record is committed. That job becomes interrupted
and requires inspection. Use list_jobs after a lost response; never treat a stale progress
timestamp as proof a running job can be safely replayed.

## Modeling examples and live acceptance

- `examples/parametric_spring_cup.py`: constrained annular sketch, named diameter/wall/height,
  change-and-restore diameter check, geometric selection, exports and exact-size screenshot.
  It is an integration test part, not the finished spring cup or extruder.
- `examples/inspect_existing_assembly.py`: full topology report saved as JSON.
- `examples/motion_check_template.py`: substitute inspected joint/body/occurrence references,
  sample an idler's swing and save 1920×1080 frames. It contains intentional placeholders.

Live gate on your PC:

1. Open a COPY of a local native design. Inspect version/document/component references.
2. Submit the spring-cup example once with units mm. Verify constraints, diameter-driven
   geometry updates, native timeline and exported files. Open the checkpoint separately.
3. Repeat the IDENTICAL request/operation ID. Confirm the same job ID and no duplicate part.
4. Run full inspection on a nested assembly; compare occurrence poses, body dimensions and
   selected edge/face references against Fusion. Confirm repeat instances are distinct.
5. Test a known overlapping pair and a known separated pair. Compare reported distance and
   interference volume against Fusion measurements. Zero clearance alone is not proof of
   non-interference. Unsupported API states must be errors, never “clear.”
6. Drive a test hinge/slider across known positions. Compare transforms/limits and confirm
   the original pose is restored even when a check fails or cancellation is requested.
7. Verify print-oriented exports against the source, cleanup of temporary copy, appearances,
   and actual PNG dimensions. Section curves are checked separately from presentation.
8. Test checkpoint failure, an intentional script error and bridge restart during a test job.
   Confirm full traceback, partial results, interrupted state and NO replay.

Nut insertion, clip removal, screwdriver access and the complete idler swing require
explicit tool/part clearance envelopes and defined paths. Discrete pose samples do not
prove continuous collision freedom. The connector provides measurements; it does not
infer or certify all mechanical access conditions automatically.

## Development verification

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python tests/check_mcp.py
python -m compileall -q .
```

MCP SDK is bounded to major version 1, not completely dependency-locked. No OpenAI API key
is required by this server: your connected Codex client supplies the model interaction.

## Official API references

- [Autodesk threading](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Threading_UM.htm)
- [Export manager sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ExportManager_Sample.htm)
- [Interference](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Design_analyzeInterference.htm)
- [Section curves](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Sketch_projectCutEdges.htm)
- [Viewport capture](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Viewport_saveAsImageFile.htm)
- [Joint driving](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_RevoluteJointMotion_rotationValue.htm)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Local MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

## v0.5.0 shared editing

Call `inspect_document_state` before mutations and pass the returned `edit_token`.
Use `browse_cloud` and durable `cloud_operation` jobs for project/folder creation, named native
part saves, linked insertion and version updates. Full workflow, arguments and local acceptance:
[cloud workflow](../../docs/cloud-workflow.md). Requires updating both server and add-in.
