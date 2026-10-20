# Engineering extension — caller contract 1.1

Runtime 0.7.0 development; rules 1.2.0; 32 tools. Scope/task remain schema 1.0. Engineering plan and manufacturing declaration are schema 1.0. Server and add-in must both be updated. No dependency additions.

## Entry points

Call through existing `run_model_script(...)`, with document ID, component target, units and explicit current scope. Modeling still requires writer token, matching writer identity/pins and task boundaries. Read-only verification uses `mode="read_only", checkpoint_before=False` and cannot regenerate. Obtain current solved geometry before the read-only job.

| Interface | Signature / effect |
| --- | --- |
| Batch verification | `ctx.verify_engineering(plan, previous_job_id='', detail=False)`; compact result plus hash-verified JSON artifact in job results |
| Detailed retrieval | MCP `job_result(job_id, section='engineering')`; latest engineering artifact for that job. Default `section='full'` preserves prior response |
| Surface extension | `ctx.surface_audit(body, short_edge_mm, small_face_mm2, slender_width_mm, protected_entities=(), intent_plan=None)` |
| Semantic tag | Existing `ctx.tag_geometry(...)` appends `signature_tolerances=None, allow_feature_fallback=False` |
| Resolve diagnostic | `ctx.resolve_tag(name, diagnostics=False)`; default returns native entity, diagnostic mode returns reference/method/tag |
| Stage | `ctx.run_stage(stage_id, action, postcondition, protected_plan=None)`; modeling only, checkpoint before action |
| Reconciliation | `ctx.reconcile_edit(job_id)`; read-only original failed/cancelled/interrupted job, no replay |
| Checked export | Existing `ctx.export_checked(...)` appends `engineering_plan=None, previous_job_id=''`; provided plan is an additional gate |
| Identity capture | `ctx.export(filename, entity=None, capture_identity=False)`; opt-in generation-time source identity |
| Handoff | `ctx.release_manifest(model_revision, entries, checks, filename='release_manifest.json', manufacturing=None)` |

The engineering gate is opt-in. Existing unmodified callers retain their previous validation scope. A script's execution success is not design approval. Native health, geometric quality, assembly feasibility and manufacturing readiness are reported separately. Engineering helpers do not authenticate workflow approvals or update external records.

## Interface declaration and one-call example

Obtain current tokens/revisions by inspection. Tokens below are placeholders, not usable IDs. For component-local geometry outside root, include its root-context `occurrence_token` for world-space checks. Dimensions/envelopes use mm; Fusion transforms use cm. Native-coordinate semantic selectors require a separate occurrence context for world checking.

```python
def run(ctx):
    return ctx.verify_engineering({
        'version': '1.0', 'document_id': 'CURRENT_DOCUMENT_ID',
        'interfaces': {
            'wall_lower': {
                'reference': {'token': 'FACE_TOKEN'},
                'protected': True, 'protected_tolerances': {},
                'parameter_names': ['wall_thickness'],
                'dimensions': [{
                    'name': 'wall_thickness', 'nominal_mm': 2.4,
                    'lower_deviation_mm': -0.15, 'upper_deviation_mm': 0.15,
                    'provenance': 'measured', 'source': 'measurement record A',
                    'geometry_revision': 'CURRENT_OWNING_BODY_REVISION'}]},
            'wall_upper': {'reference': {'token': 'SECOND_FACE_TOKEN'},
                           'datums': ['wall_lower']},
            'pcb': {
                'reference': {'token': 'PCB_BODY_TOKEN'},
                'mating_direction': [1, 0, 0],
                'envelopes': {'connected_wire': {
                    'frame': 'world_mm', 'min_mm': [20, 10, 2],
                    'max_mm': [42, 28, 16], 'margin_mm': 0.5,
                    'source': 'connector drawing + wire bend allowance',
                    'geometry_revision': 'CURRENT_PCB_BODY_REVISION'}}},
            'cover': {'reference': {'token': 'COVER_BODY_TOKEN'}}},
        'checks': [
            {'id': 'wall_join', 'kind': 'continuous_wall',
             'interfaces': ['wall_lower', 'wall_upper'],
             'limits': {'step_mm': 0.05, 'gap_mm': 0.05,
                        'normal_angle_deg': 0.2}},
            {'id': 'connected_wire_space', 'kind': 'access',
             'operation': 'connected_wire', 'moving': 'pcb',
             'envelope': 'connected_wire', 'obstacles': ['cover'],
             'translations_mm': [[0, 0, 0]], 'max_samples': 1,
             'limits': {'max_volume_mm3': 0}}]})
```

Each interface has exactly one `reference.token` or `reference.tag`. Optional `datums` refer to other interface IDs, recursively included in dependencies. `parameter_names` declare other parameters relevant to the requirement. Every dimension requires a unique descriptive name, finite nominal and signed deviations bracketing zero, `provenance` measured/manufacturer/assumed, source and owning body `geometry_revision`. Assumed or stale dimensions downgrade an otherwise passing dependent check to unproven. Dimensions are evidence declarations, not automatic measurements/driving constraints. `mating_direction` is validated metadata; translation lists must explicitly describe the intended path. Use existing constrained modeling helpers to make dimensions drive geometry.

Map those signed dimensional contributions to existing `ctx.clearance_budget(name, nominal_mm, terms, kind='axial', allowance_mm=0)` when evaluating fit uncertainty. That helper's terms are clearance deviations (reverse signs for subtracted sizes), not raw dimensions. This extension does not infer tolerance stack signs or material/process allowances. See script-api.md.

Purchased components need an accurate functional envelope and known interfaces, not modeled pins, threads or cosmetics. Preserve richer supplied CAD if present. Sources, uncertainty and relevant connected-wire space matter more than visual detail.

## Bounded checks and intent

| `kind` | Inputs / limits | What can be concluded |
| --- | --- | --- |
| `continuous_wall` | Two planar face interface IDs; `step_mm`, `gap_mm`, `normal_angle_deg` | Plane offset, minimum separation and unoriented plane-normal agreement. Explicit wall intent required. Not general contour/minimum thickness/junction proof |
| `gap` | Two interfaces; `min_mm`, `max_mm` | Minimum-distance interval; zero does not establish absence of penetration |
| `intersection` | Two solid body interfaces; `max_volume_mm3` | Temporary BRep intersection or disjoint bounds. Positive allowance requires `intent_reason` (e.g. press fit). No persistent design mutation |
| `G1` / `G2` | Faces sharing a topological edge/context; `samples` 3–65; `normal_angle_deg`, and `curvature_per_mm` for G2 | Interior boundary samples detect tangent-plane disagreement; unsigned principal-curvature magnitude differences can reject G2. Agreement remains unproven globally, including G2 direction/sign |
| `access` | `moving`, envelope name, nonempty `obstacles`, explicit `translations_mm`, `max_samples` 1–4096, `max_volume_mm3` | Declared box overlap at poses; a single pose can pass a static envelope requirement. Multiple clear poses remain unproven between poses |

Access `operation`: insertion, removal, screwdriver, screw_insertion, connector_engagement, connected_wire, heatset, travel or stop. They classify the declared check; they do not generate trajectories. Boxes are axis-aligned in world mm, optionally expanded by margin; translation only. Rotation, cable flex, installation temperature and undeclared obstacles are untested. No occurrence moves. Conservative envelope obstruction rejects the envelope, not every possible detailed-part/tool path.

Choose the check/limits to express intent. A part seam uses a gap interval; a press fit uses a justified overlap allowance. Do not apply a smooth-wall requirement across an intentional rib, chamfer or stop. Do not accept a healthy timeline, valid solid or numerical tangency as aesthetic approval. Inspect a close-up/section where silhouette or finish matters. Failed wall checks return measured points and section hints; access checks return the obstruction's entity, pose and intersection centroid. No screenshot or section is silently created.

## Evidence reuse and output

The compact response contains conclusions, failed/unproven IDs, per-check durations, first actionable failure evidence, resolved/check/kernel counters, unchecked areas and the detailed retrieval request. Detailed files retain interface provenance, dependency fingerprints, all poses/samples, exact refs and measurements. `detail=True` returns the full report deliberately.

Reuse is allowed only when the same document, requirement, resolved geometry identity, owning body revision, occurrence placement, datum closure and declared parameter expressions match. Changed references, tolerances or envelopes invalidate the check. Unrelated component changes do not. Native health is recomputed. The last engineering report in a prior job is the reuse source; file SHA is checked before reading. Broken artifact paths/hashes fail visibly.

Dependency discovery is bounded: interface/datums plus actual body revisions/transforms and declared parameters, with the existing scope's known joint gaps. The caller must supply all relevant obstacles/parameters/dependencies; this is not a complete projection/derive/contact dependency graph. Known scope gaps downgrade aggregate pass to unproven. Unknown omissions remain an explicit limitation.

## Semantic references and interrupted edits

Optional tag signatures capture bounds, available area/length/volume, geometry type/radius and plane data. Empty `signature_tolerances={}` requires identical metrics. Numeric changes require explicit per-field tolerance (`bounds_mm`, `area`, `length`, `volume`, `normal`, `plane_offset_mm`, `radius_mm`); area mm², length mm, volume mm³, normal unitless. Strings/types must match. Signature metrics are not complete shape equivalence.

If the originating feature is unavailable, fallback requires both a captured signature and explicit `allow_feature_fallback=True`. Selection plus signature must yield exactly one candidate. Never choose the first of multiple matches. Error codes distinguish wrong_document, reference_missing, reference_ambiguous, reference_wrong_type, reference_stale and stale_feature from evaluator failures. Wrong document never authorizes a token fallback.

```python
def run(ctx):
    def cut(c):
        # Perform the bounded native feature creation here; return JSON refs.
        return {'feature': c.ref(created_feature)}
    def inspect_cut(c):
        # Evaluate actual postconditions; return pass only when proven.
        return {'status': 'pass', 'measurement_mm': measured_value}
    return ctx.run_stage('cable_exit', cut, inspect_cut, protected_plan=plan)
```

This template requires caller-supplied modeling/postcondition code. The checkpoint completes before action. Action return, postcondition, before/after observations and status are flushed to the journal. A failure reports observed model changes or unknown, with traceback. Named protected interfaces must resolve before mutation and retain declared metrics/placement afterward. Reusing a stage ID in the same job is rejected.

After uncertainty, retry the same operation ID/arguments to find the original job. Reconcile with a new read-only batch: `return ctx.reconcile_edit('ORIGINAL_JOB_ID')`. It lists completed stages not to replay, unresolved stages, checkpoints, protected comparisons and concrete blockers. It never executes old code, rolls back or blindly resumes. A corrective mutation must be a new explicit scoped operation with a changed hypothesis/method and original-job link. After an add-in restart, unsaved document identity cannot be inferred; same saved cloud file identity can support observation, not automatic recovery. Crash/restore and external effects can remain unknown.

## Manufacturing declaration

Capture native individual part identity with `artifact = ctx.export('part.step', part, capture_identity=True)` or engineering-gated `export_checked`. Identity includes document, actual body refs/revisions and metric signatures; leaf components only, no proxy/assembly exports. The optional plan gate blocks every failed/unproven declared check. It does not turn sampled G1/G2 agreement into a release pass.

For `release_manifest`, retain its existing generation-time `model_revision`, SHA and check provenance requirements. Add `manufacturing={ 'version':'1.0', 'interface_plan': plan, 'parts': {artifact['path']: part_declaration} }`. Each part declaration contains:

```python
{
  'print_orientation': {'frame': 'native_component',
                        'x_axis': [1,0,0], 'z_axis': [0,0,1]},
  'bed_contact_face': 'bed_face_interface_id',
  'protected_interfaces': ['mating_face_interface_id'],
  'allowed_support_faces': [], 'support_exceptions': [],
  'overhangs': [], 'bridges': [], 'access_constraints': [],
  'geometry_review': {'status': 'unproven', 'source': 'review record'}
}
```

Orientation axes must be nonzero/orthogonal. Bed/support IDs must resolve to faces of the exported part; protected IDs must be marked protected. All listed fields are explicit, even when empty. `geometry_review` is observed/unproven with source. The manifest rejects changed bytes or source revisions. These are revision-matched declarations: the helper does not apply orientation, verify actual bed contact or derive overhangs/bridges. Manufacturing readiness remains unproven pending slicer and physical checks. Printer profile, plate arrangement and per-object settings remain slicer-owned.

## API evidence and native limits

Implementation uses Autodesk's documented [temporary BRep operations](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TemporaryBRepManager.htm), [normal evaluation](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SurfaceEvaluator_getNormalAtPoint.htm), [curvature evaluation](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SurfaceEvaluator_getCurvature.htm) and [oriented boxes](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_OrientedBoundingBox3D_create.htm). Native evaluator behavior, empty Boolean intersections and nested occurrence transform semantics still require Fusion qualification. All helpers run inside the existing main-thread custom-event path. API documentation is not execution evidence.
