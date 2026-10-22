# K1 feedback: baseline and implementation disposition

Baseline: workbench `6db17f97543ab88857f185343df5b02484f9e421` (0.7.0).
This is a local 0.8.0 development candidate, not installed, pushed or released.
The Oct 21 text-only evidence ZIP was checked against every packaged SHA256 entry (no mismatches).
It is evidence, not a distribution or publication authorization. Private records/native IDs are not copied here.

## Source reconciliation before changes

The development snapshot differs from current upstream in exactly four included files:
`scope.py`, `tests/test_scoped_workflow.py`, the native engineering fixture, and the package
README. The first three contain MCP-K1-01/02; integrated with regressions. The older README
was not substituted for newer upstream documentation. The sole installed/development snapshot
difference is the test file; installed runtime source matches the supplied development snapshot
according to its manifest. This is dated snapshot evidence, not a live computer inspection.
The retained checked-export patch was separately reviewed and integrated with the same strict
revision recheck. It skips redundant compute only for the exact previously solved revision/
parameter state. Changed state still recomputes; stale evidence is never automatically refreshed.

## Current-state gaps and bounded changes

| Item | 0.7 baseline | Candidate change and remaining gap |
|---|---|---|
| M01 compact responses | Job result/full inventories default; rules hash reuse and assembly paging already exist | Implemented compact state/token/job/reconcile, immutable SHA reports, raw/section pages, parameter deltas, unchanged poll, byte telemetry. Other inspection tools retain existing outputs; descriptions are not claimed reduced from the project's host measurement. |
| M02 maintainable authoring | Counts/style review, no issue budget | Partial: optional adopted source/addition/attempt/time budgets for task-bound batches and narrow calls; cumulative SQLite ledger and blocked claims, retained source/history detection. Arbitrary Python remains posthoc, legacy unscoped calls are unbounded. No automatic repair-chain semantics or replacement promotion. |
| M03 progress/recovery | Durable jobs/stages exist, coarse caller progress | Partial: durable native operation events and cooperative issue time, worker heartbeat separately, restart uncertainty. Automatic instrumentation of every raw adsk call and forced interruption are unsupported. An interrupted active authoring ledger stays blocked; automatic reconciliation/clearing is not implemented. |
| M04 result attribution | Some separate statuses; late wrapper errors obscure results | Implemented durable return flush, explicit outcomes, optional presentation failure, retained file receipts, per-entity missing health handling. Unknown API health remains unproven. No whole-job replay permission. |
| M05 boundaries | GUID and exact placement comparisons; generated dimensions flagged | Partial: new native-owned model dimensions accepted only in permitted components; existing/foreign dimensions still protected. GUID-only propagation is recognized only for history-free B-rep references with stable body revisions and bounded metrics. Opaque history and unknowns still block. |
| M06 cloud/presentation | Replay-safe uncertain saves and checkpoint types already exist | Partial: first-save metadata waits for matching resolved complete cloud identity/destination, no replay; PNG raster validation and non-regenerating presentation. Real cloud/viewport behavior remains unverified; no automatic dirty-model reload. |
| M07 Boolean ownership/diagnostics | General API and experiments; project script workaround | Deferred: no native access to prove kept cutter/multi-fragment attribution or near-coincident diagnostics. Do not generalize the workaround into an untested kernel helper. |
| M08 finite junction/retained coverage | Declared surfaces/access only | Deferred: no finite-neck/ligament evaluator or complete destructive-impact inference. Existing localized checks cannot confer a whole-part pass. |
| M09 actual mesh/package | Hash/revision export declarations | Deferred: actual mesh correspondence, globally unique slicer IDs/grouping and cross-kernel contradictions need an adapter with synthetic controls. No adapter code changed. |
| M10 profile/physical start | Outside Fusion server | Deferred to slicer/execution integration. No presets, printer commands or new start route. Existing authorization/idempotency requirements remain caller-owned. |
| M11 emitted supports/bridges/evidence | Dependency-bound engineering evidence and manufacturing declarations | Deferred for chronological toolpaths/support geometry. Existing declarations and owner-reported evidence remain supported, not newly proven emitted-path checks. |

No register item is silently discarded. See `k1-fix-disposition.json` for every stable ID,
files, tests and native status. Accepted historical native evidence is distinct from current
software execution. No new physical outcome is inferred from the old running print record.

Post-smoke source follow-up: explicit ledger observation/acknowledgement is now implemented and
software-tested; it never automatically clears/promotes/replays work. Durable baselines are
required, consumed budgets/history remain, protected/history gaps block, and further work needs
a changed strategy plus remaining budget. Legacy missing baselines and unsaved cross-session
identity remain blocked. New native negative controls are prepared but not yet run; see CURRENT.md.
