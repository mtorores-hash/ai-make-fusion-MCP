# Compatibility handoff for AI_MAKE

Fusion MCP **0.8.0 development**, caller contract **2.0**, rules **1.3.0**, **32 tools** is prepared
locally, not pushed, installed or released. Scope/task and engineering-plan dictionaries stay 1.0.
Source starts from workbench `6db17f97543ab88857f185343df5b02484f9e421`, including the actual
K1 root-scope/fixture correction and retained checked-export synchronization patch.

**Breaking defaults:** `inspect_document_state`, `acquire_edit_token`, `job_result` and
`reconcile_cloud_job` now return compact summaries; `section="full"` retains the old payload.
`job_result` also accepts `report_id`, `offset`, `limit`, `after_revision`, `baseline_report_id`;
raw/JSON-pointer pages, parameter deltas and activity events are documented in k1-caller-migration.md.
Writer identity, current revisions, exact accepted reference pins and full stale-edit checks remain required.

**New helper behavior:** `ctx.native_call`/`ctx.operation` persist operation identity before native calls;
`ctx.capture(required=False)` and read-only `ctx.present` retain engineering evidence on presentation failure.
Outcomes separate execution, mutation observations, regeneration, integrity, boundary, export, engineering,
authoring, readiness and approval. Missing API checks remain unproven; a failed wrapper is not replay permission.
Optional `task.authoring` adopts per-change/cumulative feature/sketch/attempt/time budgets with a stable
project-qualified issue ID. It is posthoc for arbitrary Python, not a sandbox or full tree-quality proof.
Interrupted authoring-ledger clearing/promotion remains unsupported and blocked; do not bypass by renaming.

**Demonstrated:** current software/API-double suite, response benchmark and patch roundtrip recorded in
k1-validation.md. **Unverified:** new real MCP STDIO, loaded Windows/Fusion/cloud/kernel behavior, camera
restoration and physical manufacturing. No native Boolean attribution/finite-root or slicer/printer adapter
fix is claimed. Existing historical 0.7 native results are preserved as provenance, not new acceptance.
Workflow approvals and external graph/BOM/site/slicer/physical execution remain caller-owned. Release is
still conditional on project completion and Mauricio approving the printed design. AI_MAKE was not edited.
