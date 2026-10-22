# Caller migration: 0.8.0 development / contract 2.0

Rules 1.3.1; engineering and scope/task dictionaries remain 1.0; 32 tools. Both local server
and Fusion add-in must be updated together after release authorization. No new dependency.
This is a breaking default-output migration, hence caller contract 2.0.

## Compact output and complete evidence

`job_result(job_id='', section='summary', report_id='', offset=0, limit=50,
after_revision='', baseline_report_id='')` now defaults to compact output.
`inspect_document_state(document_id, acquire_token=False, section='summary', after_revision='')`,
`acquire_edit_token(document_id, writer_id, accepted_reference_versions=None, section='summary')`,
and `reconcile_cloud_job(job_id, version_id='', confirmation_note='', section='summary')`
keep the existing operation semantics. Pass `section='full'` for the previous inventory/result shape.
Full stale-edit fingerprints remain server-side and continue to reject parameter changes.

```python
state = inspect_document_state(document_id='actual-session-id')
writer = acquire_edit_token(document_id='actual-session-id', writer_id='cad-owner')
# Use writer['edit_token']; do not infer current revisions from omitted inventories.
page = job_result(report_id=state['detail']['report_id'], section='/parameters', offset=0, limit=50)
unchanged = inspect_document_state(document_id='actual-session-id', after_revision=state['revision'])
# Compare two saved state snapshots of the same document:
delta = job_result(report_id=new_state['revision'], section='delta',
                   baseline_report_id=state['revision'], offset=0, limit=50)
result = job_result(job_id='actual-job-id')
receipts = job_result(report_id=result['detail']['report_id'], section='/result/files')
```

Reports are immutable canonical JSON addressed by SHA256 under the existing runtime `reports/`
folder. Raw pages reconstruct the complete report: `section='raw', limit=32768`; join `text`
fields in `next_offset` order, UTF-8 encode, verify `sha256`. Cursors count characters, not bytes.
Structured pages cap at 100 entries; entries above 8192 bytes explicitly omit content and point
back to raw/subsection retrieval. Raw pages provide lossless bounded retrieval. Hash/report IDs
are different from cloud version IDs, model revisions and edit tokens. Summary blockers cap at
eight with an explicit omitted count. Counts and absence of detail are never approval.
Canonical response-byte telemetry excludes transport framing. Small inventories may have larger
summaries than raw output. Full detail still requires hashing/storage and is not a compute saving.

## Durable activity and outcome handling

```python
def run(ctx):
    ctx.record('clearance_requirement_mm', 0.5)
    value = ctx.native_call('join_gusset', lambda: build_join(),
                            target={'token': observed_target_token}, tools=[observed_tool_token])
    ctx.record('join_receipt', ctx.ref(value))
    ctx.capture('view.png', required=False)
    return {'completed_feature': ctx.ref(value)}
```

`ctx.operation(name, target=None, tools=None)` is the context-manager form. Identity must be
JSON-serializable; use observed tokens/refs, not API objects. Raw adsk calls outside these helpers
are not automatically attributed. Existing solve/export/checkpoint/script timing emits events.
Use `job_status(job_id)` while the main thread is blocked; the heartbeat is a worker observation.
A stale main-thread activity age is not a diagnosis of a failed/hung Boolean. Cancellation stays
pending until a cooperative boundary; no watchdog kills/replays the call. Events page through
`job_result(job_id, section='events', offset=<last cursor>, limit=50)`.

Terminal `status='failed'` can coexist with `outcomes.execution='completed'`, completed exports
and integrity `unproven`. Read independent outcome fields, blocker counts and the retained detail.
`mutation` is a bounded observation (true/false/null or unobserved/restart uncertainty), not a
transaction guarantee. No replay permission is granted. `ctx.record` persists values immediately;
a return value is available only once `run` returns. Required capture still raises; optional
capture records failure without erasing prior evidence. Readiness/approval remain unevaluated.

Read-only presentation example (no solve, checkpoint or appearance edits):
```python
run_model_script(operation_id='unique-presentation-id', document_id='actual-session-id',
    component_token='@root', units='mm', mode='read_only', checkpoint_before=False,
    script='def run(ctx): return ctx.present(filename="view.png", width=1920, height=1080)')
```
`present` optionally accepts literal `eye`, `target`, `up`, restores the camera, and records
before/after revision/parameter/pose observations. It does not save geometry. Native restoration
and PNG behavior are unverified in this candidate. PNG validation supports non-interlaced
8-bit gray/RGB/alpha; other formats report unproven/failed capture rather than a false pass.

## Adopted authoring budgets

Add this optional object to the existing task, using real source tokens and project-specific
limits (numbers below are an example, not defaults). Declare protected interfaces as frozen
members and required evidence in scope. Keep the same project-qualified issue ID across jobs.

```json
{
  "max_new_features": 1, "max_new_sketches": 0,
  "cumulative_new_features": 3, "cumulative_new_sketches": 0,
  "max_attempts": 3, "max_seconds": 120,
  "source_feature_tokens": ["observed-controller-token"],
  "planned_operations": ["edit controlling profile"],
  "protected_member_ids": ["mount"],
  "strategy_revision": "A", "strategy_note": "Edit the source profile",
  "budget_reason": "One purposeful addition maximum for this local correction"
}
```

`task.authoring` requires `task.issue_id`, existing permitted source features and a task baseline.
Limits/strategy are adopted caller assertions, not authenticated approvals. The ledger is keyed
by stable issue ID, with saved cloud-file/component claims where available. A new agent/job name
cannot reset it; affected blocked task-bound work also rejects omission/renaming of the issue.
Object identity, not token-text equality, measures in-run growth. History removal does not offset
additions; flattened replacements do not pass. A legitimate no-growth parameter edit can pass.
Existing user/manual geometry is never automatically removed or rolled back.

Scope without task, legacy unscoped calls, raw Python side effects and alternate APIs remain
unenforced routes. No policy means `procedural_unbounded`, never maintainability pass. Even a
budget pass establishes counts/source retention only, not coherent design intent or native
parameter behavior. The guard does not infer whether a renamed issue in a cloned document is
the same engineering problem. Unsaved cross-session identity requires manual reconciliation.

Failed completed attempts require a changed strategy and remaining adopted budget. Interrupted
active attempts require native observation followed by explicit ledger acknowledgement. Read-only
`ctx.reconcile_edit(job_id)` still inspects stages without changing ledger records. The new
`ctx.reconcile_authoring(issue_id, original_job_id='')` returns a hash-bound proposal with measured
growth, removed history, conservative elapsed time, consumed attempts and blockers. Supply the
exact original batch job ID. Narrow attempts without a job require exclusive bridge restart
recovery first. Legacy records without an attempt baseline and unsaved cross-session identities
remain blocked; no baseline is invented or ledger reset.

Submit observation using `mode='read_only'`, `checkpoint_before=False`, the current explicit
scope, and `script='def run(ctx): return ctx.reconcile_authoring("issue", "original-job")'`.
Read the full returned proposal, preserving the original checkpoint and retained model. Then
obtain a fresh writer token and submit a NEW operation with `mode='reconcile'`, current scope/task,
`checkpoint_before=False`, `validate_after=False`, and only:

```python
def run(ctx):
    return ctx.acknowledge_authoring('issue', 'observed-proposal-sha256',
                                   'Actual-state review and corrective strategy rationale',
                                   'original-job')
```

Only literal arguments and this single return call are accepted in reconciliation mode. It
changes ledger records, never geometry, regeneration or original job status. Stale observations,
live jobs, foreign/protected changes, lost source/history and unresolvable references block it.
Acknowledgement charges observed growth and interrupted wall time through terminal/restart time,
retains attempts/history, and leaves the issue blocked for the previous strategy. A distinct
corrective operation needs a changed strategy and remaining adopted budget. Exhausted budgets
are not reset. This is not repair, promotion, authenticated approval or unattended continuation.

## Matching loaded builds

`fusion_capabilities()` can now report server and native identity without a document. A supplied
inspected design ID also returns modeling capabilities. Inspect `compatible`, runtime, contract,
rules SHA and build SHA. Both processes must use the same immutable package folder/build and be
restarted/reconnected after changes. Equal `0.8.0` version strings alone are insufficient.

New clients preflight native identity before dispatch/enqueue of mutations. The native bridge
also rejects missing/foreign identity on legacy mutation requests and queued modeling/cloud
jobs, before consuming edit tokens or running scripts. Read-only inspection remains available.
An older native bridge lacking identity support cannot receive a new client's mutation. Original
operation-ID digests exclude transport identity metadata so uncertain retries still retrieve the
original job; no updated build silently replays it. Build hashes are import-time source identity,
not an authentication mechanism or proof of every in-memory API object.

`scope.parameter_names` must name existing inspected parameters. Approved new names belong in
`task.allowed_parameter_names`; add them to the current scope after creation. Empty/stale target
IDs now explain the `inspect_design()` sequence explicitly.

## Boundary and cloud limits

New ModelParameters with native `createdBy` and `component` attribution may belong to permitted
components without a user-parameter allowlist entry. Existing model/user parameters still require
explicit permission; foreign/frozen additions fail. This uses Autodesk's documented ModelParameter
[createdBy](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ModelParameter_createdBy.htm)
and [component](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ModelParameter_component.htm).

Protected GUID changes are classified as propagation only for history-free B-rep components with
stable body identity/revision, no opaque collections, unchanged placements/parameters and bounded
metric differences. Absolute roundoff limits: volume 1e-9 mm³, area 1e-10 mm², bounds/length 1e-9 mm;
placement translation 1e-8 mm, rotation/homogeneous entries 1e-10. These are numeric observation
bounds, not product fit tolerances. A changed body revision fails even at equal volume/bounds.
Authored sketches/features/joints/meshes and missing data remain unproven. No analytic shape proof.

First saves wait for a remote-resolvable matching cloud ID/version and destination metadata.
Incorrect identities fail uncertain; missing metadata waits within the existing 10-minute bound.
Reconciliation preserves original terminal status and requires the caller's explicit confirmation.
There is no duplicate save retry, automatic reload or promotion of an old version. Existing clean
linked-cloud checkpoints and self-contained unlinked F3D checkpoints remain distinct.

## Process 1.7 source alignment

Rules 1.3.1 adds the K1 caller responsibilities without new geometry validators or tool names. `fusion_capabilities()` adds `process_controls`, including schema versions, opt-in budget and reconciliation boundaries, and explicit external/unsupported checks. It applies to the loaded pair only when `applies_to_loaded_pair` is true. The runtime/caller versions remain 0.8.0/2.0; existing required identity hashes still change with this source. Both processes must match on any later authorized activation; this source change does not update a running installation. The prior native receipts qualify only their recorded build, not this alignment.
