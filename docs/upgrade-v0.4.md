# v0.4 — BRANCA verification update

Development update, 2026-09-23. Implements the first execution and verification slice of
[the supplied BRANCA lessons](branca-lessons.md). This is not a claim that the entire
roadmap is implemented. No live Windows/Fusion session was available to this change.

## Implemented

- `run_model_script(..., mode='read_only', checkpoint_before=False)` accepts a deliberately
  restricted query grammar and omits `computeAll` and mutation inventory. Full Python
  remains `mode='modeling'` and always regenerates at completion. Existing default-mode
  operation IDs retain their v0.3 request digest.
- Explicit `component_token='@root'` supports root targeting without relying on root-token lookup.
  Required strings, booleans and execution modes are validated before queue insertion.
- `ctx.synchronize(predicate=None, max_events=20, timeout_seconds=2, recompute=True)` provides
  bounded event synchronization. A false predicate fails clearly instead of silently continuing.
  `computeAll` itself is synchronous and cannot be forcibly interrupted by this time bound.
- Motion sampling regenerates geometry once, then verifies the joint value AND independently
  supplied expected root-context occurrence transforms at every pose. Restoration checks all
  original occurrence transforms, even when measurement fails. Missing expectations fail before motion.
- Optional bounded midpoint/near-contact refinement reports every remaining interval as unresolved.
  It is never continuous collision proof. Conservative AABB rejection is restricted to native root
  body pairs; nested/proxy bodies retain native interference analysis until frame contracts are
  established by live fixtures. There is no shape cache yet, so edits cannot reuse stale cached shapes.
- Timings distinguish solve, measurement, export, checkpoint and script time. These are nested
  inclusive durations (checkpoint includes export; script can include all helpers), not additive totals.
- `ctx.try_feature` imports an F3D checkpoint into a disposable document. It measures before/after
  body count, validity, volume, envelope, feature health and caller-supplied protected metrics.
  Rejected candidates close unsaved. Accepted candidates export a separate F3D; the source is not
  automatically replaced. This is trusted-code isolation by workflow, not a security sandbox.
- `ctx.clearance_budget` computes signed independent dimensional worst-case bounds, with explicit
  axial/radial/diametral semantics, fit allowance, controlling terms and hardware provenance.
- `ctx.tag_geometry` stores a semantic geometric selector on the native body; `ctx.resolve_tag`
  re-runs it and rejects missing/ambiguous matches after edits. Optional feature lineage uses
  Fusion token resolution, never token-string equality or face indices.
- `ctx.surface_audit` identifies short edges, small faces and a slender-face indicator; intentional
  functional entities remain review candidates and are never rounded automatically. This is a
  bounded surface review aid, not a complete surface/manufacturing audit.
- `ctx.release_manifest` and `verification.validate_manifest` reject mismatched generation revisions,
  modified artifact hashes, stale calculations and failed checks. They validate provenance and byte
  consistency; they do not themselves establish mesh quality, dimensional correctness or F3D round-trip.

## Still pending from the supplied roadmap

| Requirement | Current boundary / remaining work |
| --- | --- |
| Immutable shape cache | Deliberately absent until reliable native revision invalidation is tested |
| Full surface continuity | No G0/G1/G2 normal/curvature sampler, minimum wall thickness or near-coincident detection |
| Print audit | No layer-island, bridge-end, cantilever, enclosed support-path or actual slicer adapter yet |
| Assembly access paths | Joint motion checks exist; no dedicated nut/washer/clip/tool path planner or prerequisite-step engine |
| Contact categories | Caller must classify intended contact/heat-set fits/stops; no general contact policy engine |
| Parametric primitives | Existing spring-cup example retained; fastener stacks, pockets, bosses, gussets and loft library pending |
| Requirements/calculations | Tags retain requirement text and explicit clearance terms; no general requirement dependency graph or strength/spring model |
| Release synchronization | Hash/revision checks implemented; automatic CAD-change invalidation, BOM/manual generation and native/mesh round-trip gates pending |
| Presentation | Experiment before/after reuse one camera; portable saved review scenes, visibility/style control and deterministic animation timeline pending |
| Reliability patch detail | Attachment starts at P1; root targeting and typed queue validation addressed; missing P0 details not invented |

## Installation / migration

Follow [installation](installation.md). Update the complete software folder and restart both Fusion
and the MCP process. Keep your runtime database and checkpoints. Do not replay interrupted jobs.

`sample_motion` now requires `expected_world(position)`. Old calls without it fail explicitly.
This is a deliberate verification gate: requested joint values alone no longer qualify as verified poses.
The callback must calculate expected transforms from independent kinematics; copying the observed
transform into the expectation defeats the check. See the updated motion example.

## Recompute contract

Raw `adsk` modeling stays available. Modeling scripts may defer geometry regeneration while adding
features, but must call `ctx.synchronize()` **before** intermediate measurements, inspection, export
or capture whose correctness depends on those edits. A final regeneration cannot retroactively validate
an earlier measurement. Do not suppress a failed synchronization. No unchecked arbitrary-Python
read-only/fast flag exists. Direct inspection MCP tools remain read-only and do not force regeneration.

The read-only grammar is exactly one undecorated `def run(ctx): return ...`. The returned expression
may contain JSON-like literals, lists/dictionaries and calls to `ctx.inspect`, `ctx.validate`,
`ctx.minimum_distance`, `ctx.interference` and `ctx.capture`, with literal arguments only. No imports,
assignments, loops, nested function calls, attribute traversal or arbitrary Python are accepted.

```python
def run(ctx):
    return {"assembly": ctx.inspect(False), "health": ctx.validate()}
```

Submit with `mode='read_only'`, `checkpoint_before=False`, explicit document ID and `@root`.
A read-only query assumes the current Fusion state has already solved; it does not certify an
unsolved design by skipping regeneration.

## Experiment contract

```python
def run(ctx):
    def bodies(design):
        c = design.rootComponent  # Re-resolve in each document; never retain source-body objects.
        return [c.bRepBodies.item(i) for i in range(c.bRepBodies.count)]
    def build(candidate):
        candidate.parameter("test_height", "12 mm")  # Must drive an existing native feature.
    return ctx.try_feature("height_trial", build, bodies, {
        "expected_body_count": 1,
        "max_volume_change_mm3": 100,
        "max_envelope_change_mm": 2
    })
```

Set meaningful project-specific limits before running. For bores/datums supply
`protected_metrics(design)` and `rules['protected_metrics']={metric_name: tolerance}`; metrics must
be measured independently on source and candidate. Snapshot bodies must share a coordinate frame.
The archive round-trip snapshot comparison is intentionally strict and fails closed if different.
Capture is 1920×1080 by default; before/after use the candidate's same camera, but visibility edits
by callbacks are not automatically restored. Callbacks must not switch documents, save/export release
files, or mutate objects retained from the source. F3Z/linked external assemblies are not supported by
this disposable F3D path. Preserve the source checkpoint if Fusion rejects import/export/close.
A callback may be arbitrary trusted Python; the bridge cannot sandbox its OS access or prevent it
from bypassing these workflow rules.

## Tolerance and release contracts

Clearance terms are signed deviations from nominal clearance, not raw hardware dimensions:

```python
budget = ctx.clearance_budget("arm_button_head", 0.35, [
    {"name": "printed_roof", "lower_mm": -0.2, "upper_mm": 0.2,
     "provenance": "project assumption awaiting measurement", "status": "provisional"},
    {"name": "hardware_stack", "lower_mm": -0.2, "upper_mm": 0.1,
     "provenance": "supplier drawing", "status": "specified"}
], kind="axial", allowance_mm=0.05)
```

Angular, center-location, backlash and alignment effects require separate justified projections
onto the selected clearance direction. This calculator does not infer those from nominal CAD.

For manifests, each generation-time artifact needs `path`, `sha256`, `model_revision` (and preferably
`role`, such as F3D/STEP/print_STL/BOM/manual). Each check needs `name`, `model_revision`, `passed`,
and `evidence` (`measured`, `observed`, `calculated`). Use an immutable revision assigned when the
source archive is frozen (its SHA-256 can be the revision); reassign after any relevant geometry edit.
Do not relabel old outputs with a new revision. Model-revision assignment and engineering check
completeness are caller responsibilities; a passing manifest only establishes the stated consistency.

## API sources reviewed

- [Design.computeAll](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_WorkingModel_computeAll.htm): full regeneration; completion is not feature health.
- [Occurrence.transform2](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Occurrence_transform2.htm): assembly-context transform; retired transform property avoided.
- [Import to new document](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ImportManager_importToNewDocument.htm)
- [F3D import options](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ImportManager_createFusionArchiveImportOptions.htm)
- [Document activation](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Document_activate.htm)
- [Autodesk doEvents usage](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/GenerateToolpaths_Sample_Sample.htm)
