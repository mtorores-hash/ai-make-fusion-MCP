# K1 CAD improvements

Source candidate, 22 October 2026. Extends the process-alignment draft; not installed or
native-qualified. Runtime 0.8.0, caller 2.0, schemas 1.0 and 32 MCP tools remain unchanged.
Build identity changes, so both server and native bridge must match on later activation.

## Parameter-only edits

Use `ctx.edit_parameters({'existing_width': '4 mm'})` for an existing controlling
user-parameter change. It requires an explicit modeling task/edit boundary, allowed
parameter names and an active adopted `task.authoring` budget with `max_new_features=0`
and `max_new_sketches=0`. The normal source-feature/strategy/issue/cumulative budget
requirements remain. All names and expressions are preflighted before the first write;
the helper does not create parameters. It regenerates, checks history identity/counts
and protected task boundaries, and records before/after expressions.

Try the relevant representative region and inspect the geometric consequence before
repeating a risky construction. This route covers parameter changes, not arbitrary
profile rewrites or automatic history simplification. Trusted scripts can still call
the full API; this helper is not a sandbox. A solver/setter failure can leave partial
edits. Reconcile the original job; do not replay or reset issue budgets.

## Revision-bound appearance evidence

An optional `scope.required_checks` entry can use `kind: appearance`, `members`, and
unique nonempty `views`, for example `front`, `corner_closeup`, `assembled_context`.
Supply the corresponding normal `scope.evidence` record with current revisions (or
the supported geometry fingerprint), status, source, reviewer, decision_note and
`captures: [{view, path, sha256}]`. Every required view needs exactly one existing,
hash-matching capture. Capture bytes are checked; image content, view identity and
reviewer authority are caller-reported, not authenticated or judged by this code.
Use real captures from the current model and review against current appearance IDs.

Missing views, overwritten files, stale geometry or a missing review remain unproven.
`contradicted_by` records unresolved contradictory evidence and prevents a pass. Keep
the original receipt and explicit withdrawal in project history; clearing that field
requires resolving the underlying observation, not merely editing metadata.

`ctx.export_checked` now blocks failed, stale or missing required scope evidence before
writing. This closes a gap between its documented contract and its earlier implementation.
Unchecked diagnostic exports remain available with their existing truthful labeling.

## Declared solid-region probes

Engineering check `kind: solid_probe` takes one solid-body interface and a finite box:

```json
{
  "id": "declared-root-region",
  "kind": "solid_probe",
  "interfaces": ["rail_body"],
  "probe": {
    "frame": "world_mm", "source": "project junction requirement and inspected location",
    "geometry_revision": "observed-current-body-revision",
    "min_mm": [0, 0, 0], "max_mm": [2, 3, 4]
  },
  "limits": {"min_fill_fraction": 0.95}
}
```

Coordinates and threshold above illustrate syntax, not an adopted K1 criterion. Select
the actual region and threshold from engineering intent. The check intersects temporary
world-space native BRep with the declared box and compares occupied volume/box volume.
It neither modifies the design nor accepts stale probe declarations. Kernel errors are
unproven. The measured pass covers only that box; it cannot prove attachment to neighboring
regions, strength, a complete load path, minimum thickness everywhere or slicer support.
Use explicit multiple regions/sections and appropriate connectivity evidence where needed.
The feature is additive within engineering schema 1.0; inspect matching-build capabilities
before use. Old builds cannot be assumed to recognize the new check kind.

Engineering detail now records representation, evaluator revision, method and document.
Evaluator revision participates in cache fingerprints. A check's nonempty `contradicted_by`
blocks cached success and produces unproven. Project records retain the contradictory
mesh/physical evidence; Fusion does not replace the manufacturing evaluator.

## Ownership and qualification

Fusion owns native geometry and these bounded checks. Printfarm owns exact manufacturing
mesh/package correspondence, Orca transforms/effective settings, chronological toolpath
support, checked-output submission binding and per-plate readiness. Native geometry
evidence must not be promoted into those claims. Full finite-root/connectivity and
kept-tool Boolean attribution remain unimplemented.

New regressions use API doubles, an axis-aligned box fixture kernel and temporary bytes.
They exercise thin/finite occupancy, stale declarations, unavailable kernel, contradicted
cache entries, appearance freshness and blocked export, plus bounded parameter edits.
Actual Fusion solver, assembly transforms and native Boolean acceptance are pending.

Validation on this source: 200 unittest/source/API-double tests pass, including seven
new K1 CAD regression scenarios. Isolated real MCP STDIO initialization/discovery/rules,
job identity and cancellation checks pass with native identity/preflight explicitly
stubbed. No actual Fusion solver/kernel or physical printer was exercised.
