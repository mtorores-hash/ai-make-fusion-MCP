# Engineering validation — v0.7 development

## Executed evidence

Original 150-test baseline passed before changes. Final 159 tests pass (150 existing plus 9 behavioral tests). Version assertions were updated for the new rules/runtime. No duplicate inherited test classes were added. Syntax compilation and `git diff --check` pass. Patch apply/reversal is independently checked in the review package build; see package `baseline.json`.

The new fixtures use API doubles, including an exact axis-aligned-box arithmetic double. They do **not** emulate arbitrary Fusion BRep or prove native API behavior. Executed commands from `software/fusion-prompt-mcp`:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
```

Optional reproducible software metric output: set `MCP_ENGINEERING_METRICS` to an output JSON path before running the suite. Timing varies; raw recorded run: engineering-metrics.json.

| Measure | Observed in the software fixture |
| --- | --- |
| Defects | 3/3: planar wall step, blocked driver envelope, blocked connected-wire envelope |
| False positives | 0/2 controls: intentional seam and positive-volume permitted interference |
| Signature recovery | 1/1 explicit stale-feature fault with a permitted bounded metric change; duplicate candidate rejected |
| Protected geometry | Unchanged declared metrics preserved through two stage checks; changed area detected in a separate check |
| Interrupted edit | 2 action invocations; 0 replays; 1 completed stage retained, 1 unresolved stage reported |
| Verification calls | 1 Context verification call for 3 checks; 4 interfaces resolved once, 2 temporary intersections and 1 distance query |
| Latency | 9.59 ms, single local API-double run; no native speedup claim |
| JSON output | 2629 bytes summary vs 9638 bytes detailed report (about 72.7% smaller); excludes transport/polling envelopes |
| Actual MCP calls/latency | Unmeasured; real STDIO not run because MCP SDK is absent and no dependency installation was performed |
| Native Fusion cases | 0 executed; runner supplied below |

Other demonstrated behavior: related body/placement/parameter changes invalidate evidence; unrelated component edits do not; altered artifact hashes reject reuse; assumptions and unavailable evaluators remain unproven; cancellation propagates; known dependency gaps downgrade overall pass; sampled G2 agreement stays unproven, sampled 90° discontinuity fails; required engineering failure blocks export; stale source geometry rejects manufacturing handoff. Wrong-document identity is rejected.

These are small deterministic cases, not general defect-detection/false-positive rates, production benchmarks or proof that prior physical assembly problems are eliminated. No broad audit was repeatedly run as a substitute for the targeted checks.

## Real Fusion fixture procedure — supplied, not executed

File: `software/fusion-prompt-mcp/examples/native_engineering_fixtures/native_engineering_fixtures.py` (script folder includes its manifest). It uses only standard Fusion API and this candidate's helper modules. Syntax checked; actual execution remains unverified.

1. Make this candidate available to Fusion after the separately approved installation/review procedure. Stop other modeling jobs. Preserve unrelated unsaved user work normally.
2. In Fusion Scripts and Add-Ins, add the existing script folder `examples/native_engineering_fixtures`; run it. Keep the source layout intact so its relative module path resolves. Do not select the completed Reward Rocket assembly.
3. The script itself creates a fresh `MCP_Disposable_Engineering_Fixtures` document. It never opens an existing file or saves to cloud. It constructs real native sketch/extrude solids for the wall step, blocked screw and PCB/wire envelope; checks an intentional seam; injects a stale feature token after a bounded native edit; records a completed stage then fails after another mutation and reconciles without replay.
4. Review the displayed `native-result.json` path in a newly created system temporary directory. It contains actual statuses, error traceback if any, timings/bytes, reference result, protected comparisons, action invocations and local checkpoint/job paths. The fixture remains open for close-up inspection. Save the result externally if needed; never commit its private runtime journal/checkpoints.
5. Required acceptance: three defect checks fail for the declared measured cause; intentional seam passes; signature fallback resolves uniquely; protected comparisons pass; action list is exactly `one, two`; reconciliation lists `one` completed and `two` unresolved, with no replay. Inspect actual solids against measured locations. Missing/native API failures are unproven, not fixture passes.
6. Close only this disposable document after review, discarding it if desired. Do not change/open Reward Rocket. A genuine process-crash/restart test, nested transforms, native smoothness evaluators, export round-trip and installed STDIO/cloud acceptance remain separate unfinished checks. The supplied interruption is deliberate exception injection, not a real process crash.

## Remaining limits and release decision

No native/kernel/cloud/Windows installation, true process crash, STDIO or slicer test ran here. No automatic global contour/near-coincident/minimum-wall audit, full junction attachment proof, arbitrary rotation/swept collision proof or full dependency discovery was implemented. G2 is rejection-only sampling; aesthetic acceptance is manual. Protected metric signatures are bounded guards, not complete shape equivalence. Manufacturing declarations are revision/byte matched but do not establish actual bed contact, support removal, overhang/bridge correctness or printability.

Source candidate only. Do not treat execution success, 159 passing software tests or the user's completed-product test as approval to deploy or as native manufacturing qualification.
