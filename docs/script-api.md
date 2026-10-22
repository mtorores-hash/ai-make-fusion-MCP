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
    ctx.synchronize()  # Solve geometry before measuring/exporting intermediate results.
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
| `stage(label,fraction,checkpoint=True)` | Progress plus pre-stage checkpoint; linked dirty state must be saved between batches |
| `checkpoint(label)` | Unlinked: F3D archive. Linked: clean completed cloud version/reference manifest |
| `created(entity)` / `ref(entity)` | Register or obtain native references with occurrence context |
| `record(name,value)` / `warn(message)` | Structured measurements / warnings |
| `inspect(include_topology=False,scope=None)` | Selected scope or legacy full design, health, dimensions, transforms |
| `resolve(reference,world=False)` | Resolve `{token, occurrence_token}` to native/proxy geometry |
| `select_edges(body,filters,feature=None)` | Geometric predicates plus optional current feature boundary |
| `select_faces(body,filters,feature=None)` | Surface predicates plus optional current feature faces |
| `expect_one(matches)` | Reject zero/ambiguous selections |
| `validate(scope=None)` | Scoped integrity and required evidence, separately reported |
| `minimum_distance(one,two)` | World-space minimum distance in mm |
| `interference(references)` | Current-pose interference results and volumes in mm³ |
| `section_sketch(body,plane,offset,name)` | Body/plane intersection curves in an editable sketch |
| `import_step(absolute_path)` | Import real hardware into target component |
| `set_joint_limits(joint,min,max,motion,unit)` | Rotation or slide limits with explicit unit conversion |
| `sample_motion(..., expected_world=kinematics, near_contact_mm=None)` | Verify requested joint and independent world transforms, check pairs, restore pose; optionally refine |
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
Linked checkpoints are clean completed cloud version/reference manifests, not local archives.
Save and poll between linked batches; do not detach references to satisfy an experiment helper.
See [cloud workflow](cloud-workflow.md).


## v0.4 verification helpers

See [full contracts and examples](upgrade-v0.4.md) before using these helpers.

| Helper | Behavior |
| --- | --- |
| `synchronize(predicate=None,max_events=20,timeout_seconds=2,recompute=True)` | Bounded event synchronization, with optional one full regeneration |
| `try_feature(name,build,select_bodies,rules,protected_metrics=None,capture=True)` | Disposable F3D candidate with measured guards and separate accepted archive |
| `geometry_snapshot(bodies,protected=None)` | Measured body/volume/envelope/health snapshot |
| `clearance_budget(name,nominal_mm,terms,kind='axial',allowance_mm=0)` | Independent signed dimensional bounds and provenance |
| `tag_geometry(body,name,kind,filters,feature=None,role='functional',requirement='')` | Store unique semantic selector on native body |
| `resolve_tag(name)` | Re-evaluate selector; reject ambiguous or missing geometry |
| `surface_audit(body,short_edge_mm,small_face_mm2,slender_width_mm,protected_entities=())` | Located review candidates, not full continuity or print audit |
| `release_manifest(model_revision,entries,checks,filename='release_manifest.json')` | Validate generation revisions/hashes and emit manifest |

`from FusionPromptBridge import verification` provides numerical policies to external scripts
when the software folder is on Python's import path; inside Fusion use the ctx methods or a
relative add-in import appropriate to Fusion's module namespace. No new Python dependencies.

## v0.4.1 modeling hygiene

Read [modeling rules](modeling-rules.md) before authoring. Contracts: [hygiene](modeling-hygiene.md).

| Helper | Behavior |
| --- | --- |
| `audit_hygiene(scope=None)` | Read-only scoped automated subset; no regeneration/repair |
| `require_hygiene(strict_reviews=False,scope=None)` | Record audit; raise on errors/incomplete inspection, optionally reviews |
| `export_checked(filename,entity=None,manual_review_note='',strict_reviews=False,scope=None)` | Synchronize, require audit/manual note, then export and record report/hash |

`audit_hygiene` is also allowed in restricted read-only batches. Plain exports/checkpoints remain
available for recovery/work in progress and never imply full-standard compliance.

## v0.6.0 scoped authoring and shared-edit contract

Use [caller contract 1.0](caller-contract.md): acquire a writer token separately, pass explicit
scope/task/pins, and preserve current revisions and caller evidence. Implicit batch scope is
target-only and unbounded; use explicit scope for checked deliverables. Required checks are
caller-selected for the milestone. If a script computes fresh evidence, it may update its
`ctx.selection.spec['evidence']` with actual source/revision records before final validation;
never relabel an old measurement with a new revision. Fetch current component revisions after
regeneration. Post-batch integrity and evidence status are separate from execution/approval.

Additional helpers:

- `ctx.parametric_circle(name, diameter_parameter)`: native component-owned constrained circle,
  using an existing named length parameter; checks full constraint after regeneration.
- `ctx.evidence_fingerprint(member_ids)`: conservative BRep/placement/declared-parameter reuse
  signature; complete dependency mapping still required. Allowed in restricted read-only mode.
- `ctx.retire_occurrences(occurrence_tokens, reason, replacement_id='', dependency_review_note='')`:
  explicit task/checkpoint required; conservative Remove-feature lifecycle operation. Use the
  dedicated durable tool for the normal caller path.

Linked checkpoints and unsupported experiments: [cloud workflow](cloud-workflow.md).
Native solver behavior is still unverified: [prepared acceptance](disposable-acceptance-v0.6.md).

## Engineering extension (0.7 development)

Exact helper signatures, plans, examples and limits: [engineering-contract.md](engineering-contract.md). Existing helpers are retained. `surface_audit(..., intent_plan=plan)` adds declared checks; its original small-feature heuristics remain review candidates.

## 0.8 activity, presentation and issue budgets

See [caller migration](k1-caller-migration.md) for `ctx.native_call`, `ctx.operation`, `ctx.present`, optional `capture(required=False)`, adopted `task.authoring`, outcome handling and remaining limits.
## 0.8 post-smoke-test additions

`ctx.reconcile_authoring(issue_id, original_job_id='')` is a permitted read-only query returning
a native-observed, hash-bound ledger proposal. `ctx.acknowledge_authoring(issue_id, observation_id,
note, original_job_id='')` is accepted only as one literal return call in `mode='reconcile'`.
This mode requires current scope/task/writer token, forbids checkpoints/validation regeneration,
and does not run arbitrary Python. It accounts an interrupted attempt without replay, retains
budgets/history, and requires a new strategy for any subsequent corrective work. See
`k1-caller-migration.md` for the exact sequence and conservative blockers/legacy limits.

## K1 CAD follow-up contract

The later rules 1.3.2 source adds `ctx.edit_parameters(changes)`, optional appearance
required evidence, engineering `solid_probe`, evaluator provenance and contradiction
blocking. Checked exports enforce required scope evidence before writing. See
[K1 CAD improvements](k1-cad-improvements.md) for exact fields, bounds and examples.
These additive helpers require a matching supported build; prior source/native receipts
do not qualify them. Native solver/Boolean acceptance remains pending; no farm controls
or installed runtime are changed.
