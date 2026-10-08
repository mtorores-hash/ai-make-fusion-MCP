# Architecture

## Batch workflow

1. `inspect_design` returns `design_id` and `root_component.token`.
2. `inspect_assembly` / `inspect_full_assembly` identifies another component if desired.
   Select an explicit **Component** token, not an occurrence token, for modeling scope.
3. Call `inspect_document_state(design_id)` immediately before editing. Pass its single-use
   `edit_token` to the mutation. The bridge compares current state before executing code.
   `run_model_script` accepts operation_id, document_id, component_token, units, script,
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
by opening the last usable F3D checkpoint or recorded cloud version and inspecting it; automatic
restore could overwrite unrelated work, so it is intentionally not performed.

Submission idempotency prevents accidental repeated execution under normal operation.
It is not an atomic transaction across Fusion's model and SQLite: a crash can happen after
geometry changes and before the success record is committed. That job becomes interrupted
and requires inspection. Use list_jobs after a lost response; never treat a stale progress
timestamp as proof a running job can be safely replayed.


## v0.4 update

See [Execution and verification contracts and remaining work](upgrade-v0.4.md) for the latest behavior.

## Cloud operations (v0.5.0)

`cloud_operation` shares the durable queue/idempotency journal. Main-thread custom events
start API calls and poll upload futures/documents without a sleep/doEvents loop.
Individual Fusion API calls, including synchronous metadata refresh, can still block the UI. While an
upload is monitored, queued mutations wait; status tools read SQLite independently. Restart
interrupts a running job and retains partial results without resubmitting its cloud action.
`browse_cloud` and `inspect_document_state` use the same main-thread dispatcher as inspection.
Tokens cover component revisions, parameter expressions, dirty state, file/reference versions,
processing and editability. They are single-use and session-local, checked before code runs.
The full Python runner remains trusted and unrestricted. No distributed lock is claimed.

See [cloud workflow](cloud-workflow.md) for save completion, IDs, linked checkpoints and recovery.
