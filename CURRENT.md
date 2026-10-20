# Current state

Branch: `workbench`. Version **0.7.0 development**, caller contract **1.1**,
modeling rules **1.2.0**, **32 tools**. Scope/task and engineering/manufacturing
schemas remain **1.0**.

## 2026-10-20 — implementation and installation request

Mauricio authorized implementing and installing the supplied
`Fusion-MCP-v0.7.0-review.zip`. This source update adopts that reviewed package
on top of workbench `c0f7857cfcd38ef3e0c834a7ed1bfab323a8749c`; no main merge
or public release is implied. Runtime code and tests are preserved from the
reviewed candidate. Installation/status documentation is aligned here.

Implemented: declared engineering checks and interface evidence, affected-check
reuse and compact reporting, semantic signature fallback, durable staged-edit
observations and no-replay reconciliation, and revision-matched manufacturing
declarations with optional engineering export gates. Existing 32-tool surface
and dependency requirements are retained.

## Verification and actual installation status

The supplied ZIP SHA-256 is
`5cfff9bb99db2b257adcbfdbad5c87ba0634f4417944ee71b51b7ac2b781b57c`.
All 80 package source hashes matched. The forward/reverse package baseline
reconstructs the current upstream tree exactly. Independently rerun here:
**159 unit/source-contract/API-double tests passed**; Python compilation passed.
The isolated attempt to obtain the missing MCP SDK failed because this execution
environment could not resolve its package server. Real STDIO remains unrun here.

This ChatGPT session has no execution connection to Mauricio's Windows/Fusion
computer. **Installation is authorized but not performed by this source update.**
The earlier 0.6 deployment remains user-reported. Do not label 0.7 locally installed
until the actual server and add-in report matching versions after reload.
No live Fusion/kernel/cloud, Windows installation or slicer acceptance is claimed.
No completed Reward Rocket model or physical hardware was touched.

## Next executable action

Local Codex should follow `docs/upgrade-v0.7.md` using this committed source:
preserve local edits and pending jobs, back up the existing installation/config
and runtime, update both processes, reload safely, verify real STDIO and loaded
versions, then run the disposable native fixture within the authorized scope.
Do not ask for installation approval again; ask only for a genuinely unresolved
permission, unsaved-work decision or unavoidable user-interface action.
Do not reinstall the AI Make agent team or change model routing as part of this MCP update.

## Limits

See `docs/engineering-validation.md`, `docs/caller-contract.md` and
`docs/engineering-contract.md`. Scoped signatures/samples do not establish full
shape equivalence, global minimum wall thickness, continuous collision freedom,
full dependency discovery, aesthetic acceptance, printability or physical success.
Trusted Python is not sandboxed; new component definitions in bounded tasks and
nested/jointed retirement remain unsupported. Keep these limits visible rather
than disabling required checks or rerunning broad audits.
