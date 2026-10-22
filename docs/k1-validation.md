# K1 candidate validation — 0.8.0 development

## Authorized workbench transfer — 2026-10-22

The 0.8 implementation, regression tests and disposable fixture runners were uploaded
through the authenticated GitHub web UI after the user accepted browser access and enabled
local file uploads. Connector tools remained unavailable in this chat. Remote workbench HEAD
was rechecked as `6db17f97543ab88857f185343df5b02484f9e421`, matching the candidate baseline;
each subsequent commit checked the expected remote head. Implementation transfer is recorded
through `9d09c8ae4032f3aa746181502f9a6d07e2e3be26`. Documentation and ledger accompany this
transfer; earlier pending-connector/upload paragraphs below are historical observations.

This remains a private 0.8 development candidate, caller 2.0/rules 1.3.0/32 tools. 190 source
tests passed. Revised native evidence covers the real STDIO spacer, 10 bounded fixture
controls and two mismatched caller rejections, with all five spacer artifacts hash-verified.
Actual crash/cloud/physical acceptance and end-to-end native STDIO reconcile dispatch remain
unqualified. Protected child revision propagation can block ledger acknowledgement; positive
accounting was qualified only in a separate root-only fixture with injected journal restart.
All failed jobs/receipts remain retained locally; no ledger reset or replay was used.

Only repository source/docs/examples/tests are transferred. Private host configuration, queue
databases, runtime artifacts, evidence ZIPs and native CAD/PNG fixtures are excluded. The
workbench ledger stays private; no main promotion, merge, release or visibility change.

## Revised 0.8 native validation — 2026-10-22

User cleared the blocked Fusion dialogs. A fresh Fusion process loaded the separate
`fusion-mcp-0.8.0-validation-r2` bridge. Real SDK STDIO reported matching server/native
runtime 0.8.0, caller 2.0, rules 1.3.0 and implementation SHA. Exactly one live bridge
owned the shared queue; older bridges remained stopped. Startup remains disabled.

The revised build passed 10 native disposable controls and two deliberately incompatible
caller-metadata rejection controls. A new parametric spacer passed real STDIO/native
modeling, parameter perturbation/restoration, boundary/integrity checks and checked STEP;
all five output hashes were verified. No native compatibility preflight was stubbed in
this live run. Source suite remains 190 passes; its separate offline STDIO harness uses
an explicit native-preflight stub. The native example runner was corrected afterward;
product implementation files are unchanged from the 190-test run.

Three failed runs are retained: protected child revision propagation blocked ledger
acknowledgement; a harness reused a synthetic document ID across separate fixtures; and
the spacer script initially expected the older installation path. The harnesses were
corrected, fresh fixtures used, and original jobs/ledgers retained without replay/reset.
Protected-revision rejection remains a conservative limit. Positive accounting was
qualified only in a separate root-only fixture. Native ledger helper calls use private
journals; end-to-end native STDIO reconcile dispatch remains untested. Restart and capture
failures are injected, not real process-crash or viewport-failure qualification.

The revised bridge is active and configured; existing clients need reconnection. Native
fixture receipts/F3D backups stay outside the upload package. GitHub connection guidance
was supplied, but connector tools are still unavailable; no remote HEAD verification,
upload, merge or release has occurred. See `docs/revised-native-validation.json` (or
`revised-native-validation.json` from this docs directory) for actual results and limits.

## Post-smoke improvements — source validation, revised native run pending

Implemented bidirectional compatibility checks including an import-time implementation SHA,
clearer preflight errors, and a restricted authoring-ledger observation/acknowledgement path.
190 software/API-double tests pass, including actual file-transport handshake rejection before
mutation, missing/legacy queued identity rejection, stale/foreign/removed-history observations,
attempt/growth preservation, exhausted budgets, changed-strategy requirement, and writer-token
acknowledgement dispatch without regeneration. The real isolated STDIO harness also passes;
its native compatibility preflight is explicitly stubbed, so it does not qualify native handshake.
The first 179-test run had one error-text assertion failure; retaining the old recognizable
"Active document changed" phrase with the new guidance corrected that compatibility regression.

`examples/native_negative_controls` is prepared for stale-token, foreign-parameter/frozen-dimension,
interrupted-budget observation, stale acknowledgement, retained counters, changed strategy and
optional capture-failure controls. Restart-journal and capture-I/O failures are explicitly injected;
even a future pass will not establish a real process crash or diagnose native viewport failure.
The new runner remains unrun. A separately staged revised build is configured, but Fusion's
save-dialog activation failed twice ("failed to activate captured window"); UI input stopped.
All earlier disposable native documents were first exported to local F3D backups. Revised
activation is awaiting user-assisted dialog closure/reopen. The earlier spacer/fixture native
passes below apply to the pre-improvement 0.8 build only.

GitHub upload is authorized but unperformed: the requested connector is not currently available,
so current remote workbench state has not been inspected. No remote merge/release is authorized.
Portable result metadata is in `improvement-validation.json`; private host records remain outside
this package. Current client/server activation state is recorded in CURRENT.md.

## Owner-authorized installation / actual native execution — 2026-10-21

Installed locally after the user's explicit installation-and-modeling instruction. Used the
computer-use skill to launch Fusion, inspect/stop the running 0.7 registration, disable old
startup, register 0.8 and run its native fixtures. A fresh Fusion process excluded old cached
modules. Actual paths and disk hashes were captured in the native runtime gate. Fusion
2705.1.25 embeds Python 3.14.0; the existing STDIO environment is Python 3.14.7 / MCP 1.30.0.
Only one bridge was running. Existing source, jobs and production models were preserved.

| Actual native control | Result | Scope |
|---|---|---|
| Real 0.8 STDIO → Fusion batch | Succeeded | Fresh disposable standalone spacer; 32 tools, caller 2.0, rules 1.3.0; explicit root scope/task and writer token |
| Parametric sketch / solid | Pass | One fully constrained concentric sketch, one extrude/solid; 30 × 30 × 10 mm bounds |
| Analytical volume / parameter response | Pass | Bore 8 mm: 6565.928646003 mm³; bore 10 mm: 6283.185307180 mm³; original 8 mm expression/volume restored |
| Generated dimension attribution / edit boundary | Pass | Native-owned dimensions accepted in permitted root; zero boundary violations; no authoring-budget policy adopted for initial construction |
| Integrity / hygiene | Pass with reviews | No feature errors or unavailable checks; root standalone-part exception documented; three user-parameter favorite suggestions retained; no full-standard/physical approval claim |
| Export / presentation | Pass | Checked STEP and working F3D/STL plus PNG; all five file hashes including before-batch checkpoint verified; exports were not round-trip/cross-kernel qualified |
| Native K1 contract runner | Four cases pass | Owned generated dimension, checked-export solved-state observation, no observed presentation model change, camera restored |
| Native engineering runner | Declared outcomes matched | Step, driver-access and wire-clearance defects fail as intended; explicit seam passes |
| Reference recovery / preservation | Pass, bounded | Signature fallback after stale feature; declared protected signature metrics/placement unchanged |
| Interrupted-stage reconciliation | Expected conservative result | Completed stage one retained, stage two unresolved, action invocations one/two once each, replay false; interrupted outcome still requires inspection |
| Native report retrieval via real STDIO | Pass | Raw pages reconstruct SHA256; unchanged polling and durable event retrieval pass |

Private local receipts and copied artifacts are retained under `candidate-review/native-acceptance/`;
summary in `candidate-review/native-install-validation.json`, installation/rollback metadata in
`candidate-review/installation-080.json`. These are outside the package source tree. Source
tests remain the independently executed 179 software/API-double tests; native cases are separate.

Retained failures: initial capability call used an empty rather than observed design ID and was
rejected; the first scoped model job declared parameters before they existed and was rejected
before modeling. After inspecting each original result, corrected the caller preconditions and
used a fresh empty disposable document. No production geometry was touched or failed job replayed.
The initial harness returned process exit 0 for a terminal failed job; its receipt correctly
reported failed. The harness now exits unsuccessfully for a failed native model job.

The fresh candidate STDIO client was verified against installed 0.8 server source. The pre-existing
chat tool connection still returns 0.7 rules 1.2.0 and must reconnect; it was not used to qualify
0.8. Installation config now points to 0.8; unrelated config was structurally unchanged.

Native smoke success does not resolve interrupted authoring-ledger recovery, demonstrate a real
process crash, long Boolean cancellation, cloud-first-save metadata, forced optional capture
failure, all preservation/AsBuiltJoint cases, M07–M11 adapters, or physical qualification.
No print/design/release approval is inferred. The installation remains active as requested,
with 0.8 startup enabled and 0.7 startup disabled. No rollback was performed.

Post-run review-patch generation initially hit Windows' default cp1252 decoding on UTF-8
documentation. Explicit UTF-8 corrected this evidence-packaging error; installed code/native
jobs were unaffected, and the regenerated extension patch passed reverse apply-check.

## New local execution — 2026-10-21 America/Chicago

Source: extracted review archive, then the bounded native preparation changes listed below.
Interpreter: `C:\Users\mtoro\AppData\Local\AI-Make\fusion-mcp\software\fusion-prompt-mcp\.venv\Scripts\python.exe`.
Observed Python 3.14.7, MCP SDK 1.30.0. No dependency installation.

| Check | Actual result | Evidence / limits |
|---|---|---|
| Original candidate suite | 177 tests pass, 13.535 s | `candidate-review/source-tests.log`; source/API doubles/filesystem |
| Final candidate suite | 179 tests pass, 13.956 s | `candidate-review/source-tests-final.log`; two added runtime gate controls use module doubles |
| Real isolated MCP STDIO | Pass before and after preparation edits | `candidate-review/stdio-tests-final.log`; initialize, 32 tools, rules tool/resource/hash reuse, schema validation, enqueue/status/duplicate/conflict/cancel, compact/full/raw SHA and unchanged result; temporary Store; no Fusion contact |
| Response benchmark | Pass; 10 calls/case | `candidate-review/benchmark.log`; large full/summary/unchanged 287928/958/273 bytes; large summary median 2.898 ms; direct synthetic calls, excludes transport/native time |
| Evidence integrity | 88 packaged evidence hashes match | `candidate-review/local-inventory.json`; ZIP SHA256 matches original disposition |
| Source syntax / rule mirrors | 48 Python files compile; mirrors equal | compile in memory, no native imports; final source hashes recorded separately |
| Installed runtime observation | Config and running server commands target 0.7 review source | Not candidate acceptance; default add-in junction targets a different retained 0.6 tree; another retained installation is 0.4.1 |
| Native bridge observation | Capability call timed out; no Fusion process observed | Loaded module paths, Fusion version and embedded Python remain unverified |
| Shared production queue | No queued/waiting/running jobs, no request/processing files at observation | Read-only SQLite; 18 cancelled, 463 failed, 7 interrupted, 473 succeeded; no recovery/replay performed |
| Native 0.8 acceptance | **Unrun** | No activation authorized; no model was opened/modified |

Prepared changes: `native_validation.py` checks all loaded bridge-module paths, one live worker
with an open queue lock handle, and an idle bridge before fixtures create any document. Reports
include Fusion/Python versions, resolved paths and on-disk hashes. These are provenance, not
CAD pass evidence or in-memory bytecode proof; a fresh Fusion process is required after changing
source. A read-only runtime probe does not import bridge modules or acquire a queue lock.
Both runners retain failures in their result JSON. The engineering runner no longer reloads
one module in place. The K1 runner now uses a temporary camera and records its restoration.
The K1 script manifest was added; the engineering manifest now says 0.8.0. No bridge runtime
algorithm was changed. Both fixtures and the probe remain unrun in native Fusion.

Initial restricted-shell attempts could not launch Python or inspect processes/Autodesk paths.
Approved read-only/existing-interpreter escalations succeeded; those access errors did not imply
an absent SDK. `fusion_capabilities({})` first failed required-argument validation; the corrected
read-only call with an empty design ID timed out. No mutation was submitted. The empty workspace
has no workbench HEAD; a separate LocalAppData checkout has invalid HEAD and no source. No newer
checkout was overwritten, repaired or reset. No remote workbench reconciliation is claimed.

The original source manifest and forward/reverse patches remain historical archive artifacts;
do not use them as a manifest/patch for this extended tree. Local inventory and extension hashes
are separate. Historical 0.7 receipts and all native-unrun limits below remain in force.

The first extension-patch reverse check failed because Windows newline translation produced
CRLF patch text for LF additions. Regenerating the patch with LF fixed it; the reverse
`git apply --check` then passed without applying/reverting files. This was packaging validation,
not a source test failure. `LOCAL-CHANGES.patch` describes only this continuation over the ZIP.

## Historical archive validation (before this local continuation)

177 software tests pass: 159 upstream tests retained, 2 actual project root-scope regressions
integrated, and 16 new behavior scenarios. Latest recorded suite: 2.964 seconds on Python 3.12.14;
see `k1-software-validation.json` for the observed environment. Syntax and `git diff --check` pass.
The original best-practices document is byte-for-byte unchanged. Rules copies match.
These are API doubles, SQLite/filesystem and numerical controls, not native Fusion results.

## Meaningful controls exercised

| Control | Observed software result | Limit |
|---|---|---|
| Large inventory / writer guard | 10,000 parameters, compact result; changed parameter still rejects old token | No native inventory latency measured |
| Immutable detail / omissions | Raw pages reconstruct SHA256; changed-parameter delta, unchanged polling, explicit omitted blockers/large entry | Canonical JSON sizes exclude transport envelope |
| Missing health API | Unavailable entity stays unproven; a later damaged joint in the same collection is still detected | Does not invent AsBuiltJoint health capability |
| Late failure | Completed return, recorded measurement and artifact survive missing optional PNG and missing health | Synthetic artifact is explicitly not CAD |
| Slow call / cancellation | Operation start/target/tool visible while callback blocked; cancel pending; restart marks unknown and never reclaims mutation | Threaded callback is not a Fusion Boolean |
| Generated parameters | New permitted native-owned dimension accepted; foreign addition and existing unpermitted edit rejected | Native attribution unrun |
| Frozen geometry | GUID-only history-free body + roundoff accepted; real body revision, small volume change, opaque history rejected | Bounded metrics, not complete shape equivalence |
| Authoring gate | Batch/narrow overruns fail; counts accumulate, agent/job rename or omitted policy cannot clear blocked task claims; flattened history fails | Raw/unscoped paths still unbounded; no automatic ledger recovery/promotion |
| Legitimate small edit | Same live object with changed token text does not count as new history | Caller source strategy remains an assertion |
| Checked export sync | Unchanged solved state avoids repeat compute; changed parameter recomputes; propagated stale scope still rejects | Native solver/export behavior unrun |
| First save | Delayed remote metadata completes one save; wrong destination stays uncertain/blocked | API doubles, not actual cloud persistence |
| PNG / presentation | Header-only and malformed raster fail; valid raster passes; read-only missing capture does not solve or change observed model | Native camera/viewport path unrun |

All specified positive/negative software controls matched their assertions. This is not an
estimated real-world defect detection rate or false-positive rate. Reference recovery and
protected stage no-replay regressions from 0.7 were retained, not duplicated to inflate counts.

## Actual response measurements

`python tests/benchmark_responses.py`, ten direct calls/case; reproducible raw data is in
`k1-response-metrics.json`. One logical call returns the summary, one returns the unchanged poll.

| Parameters | Full bytes | Summary bytes | Unchanged bytes | Median summary generation | Full raw pages (32768 chars) |
|---:|---:|---:|---:|---:|---:|
| 10 | 378 | 949 | 267 | 0.071 ms | 1 |
| 10,000 | 287,928 | 958 | 273 | 2.611 ms | 9 |

Summaries reduce large wire inventories, not validation/fingerprint work. Small summaries have
metadata overhead. These are canonical UTF-8 sizes and local Python time, not MCP transport,
Fusion latency, model-token usage or billing. Current source has 32 tool descriptions totaling
9,934 characters; the project's approximately 54,000-character host exposure is a different
measurement, so no schema/token saving is inferred by subtracting the two.

## Historical evidence versus new native acceptance

The supplied corrected 0.7 native receipt reports three detected defects (step, screw access,
wire clearance), an intentional-seam pass, unique reference recovery/protected comparison,
and preserved completed stage/no replay. Its defect-case match flag is true. This is useful
historical evidence for MCP-K1-01/02 and the old bounded checks, not acceptance of the new code.
The original failed native result was retained in the user's evidence bundle; no nicer result
was substituted for its history. Private native IDs and full project records are not republished.

Real `tests/check_mcp.py` for this candidate is **unrun**: SDK absent, installation prohibited.
The existing real-STDIO test is updated for compact default/full/hash retrieval and remains
ready for the already-installed environment. Source registration/binding checks are not STDIO.
Both native runners are **unrun**: `examples/native_engineering_fixtures` preserves the corrected
root-scope fixture; `examples/native_k1_contract` adds generated dimension, checked export and
presentation observations in a new disposable document. They reject a mismatched loaded source.
No Fusion connection was available and no production assembly was opened or changed.

Cloud-first-save confirmation, native ownership/revision behavior, long Boolean timing and camera
restoration need separately authorized native acceptance. Manufacturing mesh/slicer/support/profile
and physical execution adapters are deferred (M07–M11). The new opt-in authoring gate cannot clear
an interrupted active ledger; this remains a concrete workflow blocker, not an automatic retry.
Final printed-design approval and release/deployment remain pending. See `upgrade-v0.8-review.md`.
