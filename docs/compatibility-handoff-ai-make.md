# Compatibility handoff for AI_MAKE

Pushed with Mauricio's approval to workbench in `mtorores-hash/ai-make-fusion-MCP` based on workbench `b15d491fe87fd4b1a1953ea148378f045f621f14`. **Source is on workbench; not merged to main, installed or live-Fusion tested.** Runtime **0.6.0 development**, caller contract **1.0**, rules **1.1.0**, **32 tools**. AI_MAKE was not edited.

New tools: `acquire_edit_token(document_id, writer_id, accepted_reference_versions=None)`, `release_edit_token(document_id, writer_id, edit_token)`, `reconcile_cloud_job(job_id, version_id='', confirmation_note='')`, and durable `retire_occurrences(operation_id, document_id, occurrence_tokens, reason, dependency_review_note, scope, task, edit_token, replacement_id='', accepted_reference_versions=None)`.

Existing `run_model_script` and six narrow modeling tools append optional `scope`, `task`, `accepted_reference_versions`. Inspection/audit/validation take `scope`; `inspect_full_assembly` adds `include_context`; `get_modeling_rules` accepts `known_sha256`. **Migration:** `inspect_document_state` now observes by default. New writers acquire separately; old callers explicitly use `acquire_token=True` and legacy writer. Upgrade both processes together.

Caller supplies selected targets/relevant dependencies, tokens and current component revisions, membership (`active/retired/archived`), maturity (`working/frozen`), roles, declared parameter dependencies, milestone checks and source/revision evidence. Task supplies task/baseline/writer IDs, allowed/frozen members, permitted parameter names and optional cooperative time bound. Approval references are unauthenticated caller metadata. Dependency completeness, frozen reopening and approval decisions remain caller-owned.

Cloud mutations take matching `writer_id` and accepted current reference pins in `arguments`. Accepted older dependencies are preserved; stale editing targets are rejected. Dirty/stale recovery is save with pins → update one reference → refresh pins/save → repeat. Uncertain saves block mutations until original-job/version reconciliation; never replay under a fresh ID. Linked checkpoints are cloud manifests, not standalone archives.

Results separate script completion, integrity validation, evidence status/gaps, edit-boundary violations and approval status. Scope/exclusions/current revisions accompany audits and checked exports; global new damage fails even outside task scope. Trusted Python is not sandboxed: arbitrary edits are detected afterward, without rollback. Retirement supports only top-level non-derived leaf occurrences without live joints/rigid groups; lifecycle records return `external_records_updated:false`. Caller reconciles graph/BOM/context/site.

Example implemented query request (synthetic IDs; full fixture request/result are in `examples/scoped-validation.*.json`):

```json
{"operation_id":"fixture-scoped-validation","document_id":"doc","component_token":"carrier","units":"mm","mode":"read_only","checkpoint_before":false,"validate_after":true,"script":"def run(ctx): return ctx.validate()","scope":{"version":"1.0","mode":"selected","targets":["carrier"],"dependencies":[],"members":[{"id":"carrier","component_token":"carrier","revision":"r1","membership":"active","maturity":"working","role":"authored"}],"parameter_names":[],"required_checks":[],"dependency_review":"complete"}}
```

Corresponding API-double result fields: `status:succeeded`, `execution_status:completed`, `regeneration_performed:false`, `validation.validation_status:pass`, `validation.evidence_status:pass`, `validation.scope.mode:selected`, `approval_status:not_evaluated`. These prove the fixture's schema/control flow only, not geometry or whole-assembly readiness.

Implemented helper `ctx.parametric_circle` supplies native component-owned driven constraints; root primitives remain concepts. Checked export accepts explicit scope; minimum functional source-grounded envelopes are valid; exact fasteners come after joining/access intent; unchanged evidence may be reused conservatively. No global workflow, model roster, printer inventory, budget/scheduler or GitHub logic was added.

Unverified: new real MCP STDIO handshake/schemas (SDK absent; no install authorized), installed Windows/Fusion API/kernel behavior, cloud concurrency/late upload association, native constraints/Remove and real exports. No full projection/derive dependency discovery, nested retirement, new component definitions inside bounded tasks, arbitrary-Python prevention, distributed locks or automatic CAD rollback. Use the repo's caller contract and separately approve its disposable acceptance procedure before deployment.
