# Fusion MCP caller contract 1.1

Runtime **0.7.0 development**, rules **1.2.0**, **32 MCP tools**. Both server and add-in must match. This contract adds ordinary JSON dictionaries to existing tools; it introduces no external workflow service or database schema. All Fusion API calls remain on the main thread.

## Additive engineering extension in 1.1

See [engineering-contract.md](engineering-contract.md). Tool count stays 32. Scope/task JSON remains version 1.0. New batch helpers, optional export/manifest fields and `job_result(job_id, section="engineering")` are additive. Existing 1.0 callers retain behavior; new engineering gates require explicit caller plans. No silent global engineering certification is introduced.

## Tools and migration

| Interface | Implemented change |
| --- | --- |
| `inspect_document_state(document_id, acquire_token=False)` | Observation by default; does not acquire, replace or invalidate a writer token. **Changed v0.5 default.** |
| `acquire_edit_token(document_id, writer_id, accepted_reference_versions=None)` | New: single-use optimistic writer token. Same writer and unchanged state reuse it. Different writer must wait for explicit release. |
| `release_edit_token(document_id, writer_id, edit_token)` | New: release exact unused writer token. |
| `reconcile_cloud_job(job_id, version_id='', confirmation_note='')` | New: observe original uncertain save and optionally record caller-confirmed completion; never replay it. |
| `retire_occurrences(operation_id, document_id, occurrence_tokens, reason, dependency_review_note, scope, task, edit_token, replacement_id='', accepted_reference_versions=None)` | New durable batch using native Remove features; top-level leaf occurrences only. |
| `run_model_script(..., scope=None, task=None, accepted_reference_versions=None)` | Existing arguments retained. New scope, task boundary and accepted cloud pins. |
| `rectangle_sketch`, `circle_sketch`, `extrude`, `set_parameter`, `fillet_edges`, `create_joint` | Same three appended optional fields. Scope-only calls check selected ownership and integrity; scope plus task adds bounded edits. |
| `audit_modeling_hygiene(design_id, scope=None)`, `validate_model(design_id, scope=None)` | Explicit selected/full-design contract. Omitted scope keeps legacy full-design queries. |
| `inspect_full_assembly(..., scope=None, include_context=False)` | Occurrences/parameters returned on first page or explicit request; follow `next_offset`. Component revisions included. |
| `get_modeling_rules(known_sha256='')` | Matching SHA returns metadata plus `unchanged:true`, omits text. Changed SHA returns complete text. Resource always returns full text. |

All exact signatures are in [tool-reference.md](tool-reference.md). Original 28 tool names remain. `inspect_document_state(..., acquire_token=True)` retains the v0.5 writer path with writer ID `legacy`; legacy mutations omit task and pins. Calls relying on the old implicit token **must migrate**. Tokens/document IDs are session-local and lost on add-in restart.

No-scope modeling batches now validate the selected target plus a cheap global new-damage sweep. The resulting implicit scope has `dependency_review:not_supplied`: no claim of complete subsystem evidence. Explicit scope is required for checked deliverables. No-scope inspection/hygiene remains legacy whole-design authored checking; supplier exemptions require explicit roles. `validate_after=False` never disables modeling regeneration/integrity. Read-only grammar still prevents mutation and never regenerates.

## Scope dictionary

```json
{
  "version": "1.0",
  "mode": "selected",
  "milestone": "caller-defined-detail-review",
  "targets": ["carrier"],
  "dependencies": ["motor"],
  "members": [
    {"id":"carrier","component_token":"TOKEN_FROM_FUSION","revision":"CURRENT_REVISION","membership":"active","maturity":"working","role":"authored"},
    {"id":"motor","component_token":"MOTOR_TOKEN","revision":"MOTOR_REVISION","membership":"active","maturity":"frozen","role":"purchased"}
  ],
  "parameter_names": ["insert_diameter"],
  "dependency_review": "complete",
  "required_checks": [{"id":"carrier_mounting_fit","members":["carrier","motor"]}],
  "evidence": [
    {"id":"interface_envelope:motor","status":"pass","source":"supplier drawing revision A, reviewed interfaces","revisions":{"motor":"MOTOR_REVISION"}},
    {"id":"carrier_mounting_fit","status":"pass","source":"measurement record URI or description","revisions":{"carrier":"CURRENT_REVISION","motor":"MOTOR_REVISION"}}
  ]
}
```

IDs are caller-owned opaque part identifiers. Component tokens resolve native definitions; never use an edge index or visibility as membership. Each active component appears once, even if it has multiple instances. Use occurrences to distinguish instances. `revision` must equal the inspected `Component.revisionId`; token strings can change, and the implementation compares resolved API objects for identity.

- `membership`: `active`, `retired`, `archived`; separate `maturity`: `working`, `frozen`.
- `role`: `authored`, `purchased`, `reference`, `environment`, `clearance`, `fixture`, `presentation`. Untouched non-authored roles receive source/interface evidence checks, not supplier naming/sketch reconstruction demands. Changed non-authored components receive authored hygiene in batch audits.
- `targets` must be nonempty. `dependencies` and `parameter_names` name relevant inspected dependencies. Additional active members may describe protected/frozen boundaries without becoming validation targets.
- `mode:full_design` must enumerate every currently occurring definition including root as a target/dependency. Legacy omitted scope also sees history definitions and does not implement role exemptions.
- A retired definition still present in the evaluated assembly is rejected; hide/suppress/name changes do not retire it. Harmless history-only definitions can be recorded as retired/archived and excluded with a reason.
- Joint-connected omitted peers create an evidence gap. Projection/derive/interface completeness remains caller-reviewed; `dependency_review:complete` is a declaration, not an automatic proof.

`required_checks` are supplied for the approved milestone. Missing, duplicated, failed or stale required evidence is unproven/failing. Non-authored relevant parts automatically require `interface_envelope:<member-id>`. Evidence must include `source` and exactly the dependency revisions for that check. `not_applicable` additionally requires `applicable:false` and a reason on the required check, and a reason on its evidence record; it remains not-applicable, never a pass or quality waiver.

Optional `geometry_fingerprint` from `ctx.evidence_fingerprint(member_ids)` can preserve evidence across component-name changes. Keep the complete `revisions` member mapping even with a fingerprint. It hashes BRep identities/revisions, instance transforms and all declared parameter expressions. Geometry/placement/parameter changes invalidate it. Mesh/sketch-only components are unsupported. Body/appearance metadata may conservatively invalidate it, and token representation changes may too. Caller must declare all functional dependencies; no universal fit-cache guarantee is made.

## Task dictionary and enforcement

```json
{
  "version":"1.0", "task_id":"TASK-42", "issue_id":"IF-7", "attempt":1,
  "baseline_id":"caller-baseline-12", "writer_id":"codex-writer",
  "allowed_member_ids":["carrier"], "frozen_member_ids":["motor"],
  "allowed_parameter_names":["insert_diameter"],
  "approval_reference":"caller record, not authenticated by MCP",
  "max_seconds":120
}
```

The time value is an **example caller-authorized limit**, not project policy. It is positive/finite and checked only at cooperative batch checkpoints; no forced interruption of a kernel call or tight Python loop. Narrow synchronous tools do not enforce this time bound. `baseline_id`/task/issue/attempt/approval strings provide correlation; actual preconditions use Fusion revisions and edit-token digest. They do not authenticate a person, approval, baseline system, budget or Filter override.

| Boundary | Actual guarantee |
| --- | --- |
| Before supported narrow operations/helpers | Check explicit scope/current revisions, target ownership, allowed components and named parameter where supported; reject declared frozen edits. |
| After scoped narrow operations / task-bound scripts | Compare component revisions, parameter expressions, occurrence placement/removal/addition; detect out-of-set/frozen changes and new definitions. New integrity errors anywhere fail. |
| Arbitrary Python | Trusted full API, **not sandboxed**. Detection is afterward and cannot guarantee rollback, catch change-then-restore edits or protect another document/filesystem. |
| New definitions under a bounded task | Contract 1.0 conservatively rejects new component definitions afterward. Prepare/inspect approved components first, then acquire a bounded task. Legacy unbounded creation is still available; it provides no task-boundary guarantee. |
| Root/ancestor edits | Include owners actually affected (root for root tools, joint creation and retirement). Revision propagation may conservatively flag ancestor edits; inspect actual Fusion behavior. |
| Cloud operations | Writer/token/pins protect document state. `arguments.task_link` is correlation only; cloud insert/update/copy do not enforce modeling member boundaries. |

Exact fasteners, approval cadence, reopening frozen parts, PDS, budget, BOM, graph/site and GitHub synchronization stay outside the MCP.

## Results and checked exports

Job `status` is transport/execution lifecycle (`queued/running/succeeded/failed/cancelled/interrupted`). Batch result separately contains `execution_status`, `regeneration_performed`, `validation`, `edit_boundary`, `approval_status`, `operation_id`, `task`, timings, created references, measurements, artifacts and traceback. A script can complete while its job fails required postconditions. `partial_changes_possible` is true on unsuccessful jobs; no rollback is implied.

`validation.validation_status` covers **feature/joint integrity only**. `evidence_status` and `evidence_gaps` separately report required functional evidence. `new_errors` anywhere, `relevant_preexisting`, `unrelated_preexisting`, warnings and unknowns remain distinguishable. A standalone observation has no earlier baseline and cannot infer when an error appeared. Hygiene separately returns `applicable_checks`, `not_applicable`, exclusions, scope and current revisions; `full_standard_verified` remains false.

`ctx.export_checked(filename, entity=None, manual_review_note='', strict_reviews=False, scope=None)` requires a matching nonempty current scope, actual native component/body and manual review note. It regenerates, rechecks scope freshness, integrity, edit boundaries and hygiene/evidence before writing. Exporting a parent must include every exported descendant as a target; a selected body stays bounded to its owner. A successful scoped export is not whole-assembly approval. Plain `export_model`, `ctx.export`, checkpoints and print-copy exports remain unchecked working/recovery paths and must never be labeled checked deliverables.

`ctx.parametric_circle(name, diameter_parameter)` builds a component-owned, origin-coincident, dimension-driven circle using an existing named length parameter, regenerates and checks full constraint. Rectangle/circle/root-extrude tools remain labeled concept primitives. Broader native modeling is still trusted adsk scripting, not a separately validated wrapper per operation.

Retirement requires explicit task/scope, root plus source definitions permitted, checkpoint, reason and dependency-review note. Only top-level non-derived leaf occurrences without live joints/as-built joints/rigid groups are supported. Remove features preserve shared definitions/history and source files; survivors and placements are checked. Last-instance retirement returns `current_scope`, `retired_member_ids`, excluded retired-only checks and current occurrence verification. Mixed surviving interface checks become stale and need renewed evidence. Lifecycle reports say `external_records_updated:false`; caller must reconcile its records. Nested/subtree and fully automatic projection/derive disentanglement remain unsupported.

## Examples and caller sequence

1. Observe document, inspect current component revisions and read rules (reuse SHA only on an exact match).
2. Caller supplies approved scope, dependency/evidence/milestone inputs and permitted/frozen task boundary.
3. Acquire token with the same `task.writer_id` and accepted reference map used on the request.
4. Submit one durable script/retirement ID; poll original job. Repeating exactly the same request returns the same job; changing its token/content with the same ID is rejected.
5. Inspect actual status, evidence and boundary results. Refresh scope revisions after edits. Record fresh checks or reuse proven unchanged evidence. Check export separately when ready.
6. Save completed versions using [cloud workflow](cloud-workflow.md). Reconcile uncertain saves before any new mutation.

[Example request](../software/fusion-prompt-mcp/examples/scoped-validation.request.json) and [actual API-double result](../software/fusion-prompt-mcp/examples/scoped-validation.result.json) exercise this schema. Their document/tokens/revisions are synthetic fixture IDs, not live CAD evidence; replace them with observed Fusion values. Native acceptance is [prepared, not executed](disposable-acceptance-v0.6.md).
