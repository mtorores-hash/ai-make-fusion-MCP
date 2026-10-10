# Fusion cloud workflow — v0.6.0

Fusion projects, named native part documents and linked assemblies let the human edit a part and the AI resume from the actual geometry. Do not automatically rebuild existing models, detach links, or replace occurrences/joints with independent copies. Cloud saving is independent of GitHub synchronization.

## Identity and observation

Use `browse_cloud` for hubs/projects/folders/files and `cloud_operation` for durable actions. File `id` is persistent lineage identity; `version_id` opens one specific version; `document_id` and entity tokens are bridge/Fusion session identities. Preserve the full mapping and save descriptions. Project creation ensures Assembly, Parts and Purchased Components folders. New named part documents are preferable to later migration from internal assembly definitions.

`inspect_document_state(document_id)` observes without touching writer ownership. `acquire_edit_token(document_id, writer_id, accepted_reference_versions)` acquires/reuses a baseline for one writer. Pass matching `writer_id` and pins inside cloud-operation `arguments`; modeling takes writer identity from `task.writer_id`. Legacy callers explicitly use `acquire_token=True` and omit task/writer/pins. A different writer must request explicit release; a restart clears all leases. This is optimistic same-process coordination, not distributed locking.

Tokens are consumed at mutation preflight. Intervening component/parameter/document changes, unsaved referenced documents, target version changes, read-only/in-use/processing targets and token replay stop the write. Do not edit interactively while a batch is executing. A dirty current target can be acknowledged and saved; the tool never discards/reloads unsaved edits.

## Accepted versions and preserving a dirty/stale assembly

`accepted_reference_versions` maps stable file IDs to **currently referenced exact integer versions**. It permits intentional older dependencies while reporting newer available versions. It cannot authorize writing a historical editing target. Mixed versions of one file inside a hierarchy cannot use a single file-level pin: edit the owning subassembly deliberately. Unpinned stale dependencies block normal modeling/saving.

For an assembly with dirty work and outdated references A and B:

1. Observe all versions; decide explicitly to preserve its current pins, for example `{A:2,B:4}`. Acquire a writer token with those pins.
2. `cloud_operation(operation_id, 'save', {document_id, edit_token, writer_id, accepted_reference_versions, description})`. Existing files save in place: omit destination/name. Poll until `cloud_complete:true`; retain exact returned file/version IDs. This preserves dirty work with its original references.
3. Acquire a fresh token/current pins, then `update_reference` with `file_id:A` and inspected `expected_latest_version:3`. The operation first records the clean assembly's cloud checkpoint; it selects that exact processed version, not a moving latest value. Inspect joints, placements and relevant geometry.
4. The assembly is now dirty. Acquire a fresh token with **updated** pins `{A:3,B:4}` and save/poll again. Do this before the second reference update.
5. Update B, inspect, acquire pins matching both current references and save/poll again. Do not skip the intervening save or drop the accepted older pin on the remaining dependency.

Numbers are examples, not fixed project versions. Every intentional new action gets a new operation ID; a retry of an uncertain submission uses the identical original ID/request. Saving creates recovery evidence, not design approval.

## Supported cloud arguments

| Action | Required action arguments beyond `operation_id/action/arguments` |
| --- | --- |
| `ensure_project` | `hub_id`, `name` |
| `ensure_folder` | `hub_id`, `project_id`, parent `folder_id`, `name` |
| `open` | `version_id`, `expected_version`; optional `allow_historical:true` for intentional inspection |
| `save` | `document_id`, `edit_token`, optional `description`; first save also `hub_id/project_id/folder_id/name` |
| `save_component` | First-save fields plus `component_token`; saves independent native copy, never migrates occurrences/joints |
| `insert` | `document_id/edit_token/version_id/expected_version`, `transform_cm` (16 finite values); linked file must be same project; historical insertion also requires `allow_historical:true` and matching `accepted_insert_version` |
| `update_reference` | `document_id/edit_token/file_id/expected_latest_version`; exactly one direct reference |

All document mutations additionally accept `writer_id` (default `legacy`), `accepted_reference_versions` and optional `task_link` for correlation only. Insert/update require a clean fully processed cloud save. First-save/copy destinations reject existing filenames instead of silently making duplicates. Dirty already-open documents are left intact by `open`; historical inspection never permits overwriting a newer target.

## Uncertain saves, durable recovery and checkpoints

Save intent and `uncertain:true` are journaled **before** calling Fusion save/saveAs/saveCopyAs. Completion requires the exact expected cloud version and `isComplete`. A timeout, interrupted bridge, failed call or cancelled monitor may leave a late upload. New cloud/modeling mutations are blocked while any journaled uncertain save remains. Observation/jobs/browse remain available. This is conservative across documents.

Inspect original `job_status/job_result`, Fusion Data Panel/history and actual contents. Call `reconcile_cloud_job(job_id, version_id)` first to observe. It checks completion, expected version and (for an existing target save) stable file identity. Only after the caller verifies the intended contents, call again with a nonempty `confirmation_note`. This records caller evidence and clears the block; original failed/cancelled/interrupted execution status is preserved. It never replays the save or claims authenticated approval. First-save/component-copy association requires caller verification because there is no preexisting destination lineage. A missing/failed upload with no completed expected version cannot be automatically reconciled; preserve the journal and use explicit manual recovery. Do not erase the journal, invent a fresh-ID retry or claim no save occurred.

v0.5 journals lack the new uncertainty marker; the update cannot retrospectively prove old pending outcomes. Inspect/reconcile outstanding old jobs and actual cloud history before upgrading. Local operation-ID deduplication is not a transaction across Autodesk cloud and SQLite; a crash after native geometry mutation can still leave a partial interrupted script requiring inspection.

Linked checkpoints are **JSON manifests** of clean completed assembly and reference versions, not self-contained local archives or automatic rollback. Dirty linked checkpoints stop; save/poll between batches. Local unlinked checkpoints remain F3D archives. `ctx.try_feature` rejects linked experiments before regeneration, snapshot or mutation. Alternative: work on a separately authorized unlinked local part copy with a self-contained archive, review it, and deliberately integrate it later; no automatic detach, assembly rebuild or joint migration.

See [disposable acceptance](disposable-acceptance-v0.6.md) and [installation/rollback](upgrade-v0.6.md). Native cloud behavior remains unverified in this development session.
