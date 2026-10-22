# 0.8.0 review candidate: preparation, installation and rollback

## Executed local installation — 2026-10-21, subsequent user authorization

The user explicitly requested installation in Fusion and modeling to test the MCP. This overrides
the previous local no-install restriction; release/push conditions remain unchanged. Installed
source into a new `C:\Users\mtoro\AppData\Local\AI-Make\fusion-mcp-0.8.0-review` folder, resolving
under the packaged app's LocalCache tree. Config retains the existing Python command and now
targets that folder's `server.py`. Old 0.7 source and legacy junctions remain untouched.

Observed actual 0.7 registration before switching, stopped it/disabled startup, restarted Fusion,
registered/ran matching 0.8, and verified actual native paths/versions. Both disposable runners
and a real STDIO/native parametric spacer test passed their declared checks. 0.8 is left active
with startup enabled as requested; automatic rollback from the earlier temporary proposal was
not performed. Existing connected clients still need reconnection to replace their old server.

Backup: `LocalAppData/AI-Make/backups/mcp-080-20261021-204224` (resolved LocalCache path recorded in
`candidate-review/installation-080.json`). Includes old 0.7 source, config, add-in XML and consistent
SQLite backup. Existing 14.8 GB artifacts remain in place with inventory, not a second full copy.
Native receipts and failures are in `candidate-review/native-install-validation.json` and
`native-acceptance/`, outside package source. No installed code drift was detected afterward.

Rollback remains available: first reconcile pending work and stop the 0.8 bridge at an idle
boundary; disable its startup, restore only the backed-up fusion config table, restart Fusion
and activate the retained matching 0.7 review add-in, with its former startup preference enabled.
Verify paths/version 0.7/caller 1.1/rules 1.2 and reconnect the caller. Retain the newer runtime DB,
events/artifacts; never overwrite it with the backup or bypass 0.8 blocked authoring work. No
rollback has been executed. The earlier proposal below is preserved as pre-authorization history.

## Concrete temporary native-validation activation — proposed, NOT executed

Prepared 2026-10-21 America/Chicago. This is the single proposed activation for user approval;
it is a temporary test session, followed by rollback to the configured 0.7 source. It does not
authorize permanent deployment/release or establish printed-design approval. The user's current
no-install restriction is why execution stops here. Historical release instructions follow below.

Observed configuration and targets:

- Config: `C:\Users\mtoro\.codex\config.toml`, only `[mcp_servers.fusion]` is in scope.
- Existing Python (keep unchanged): `C:\Users\mtoro\AppData\Local\AI-Make\fusion-mcp\software\fusion-prompt-mcp\.venv\Scripts\python.exe` (3.14.7, MCP 1.30.0).
- Existing server/rollback source: `C:\Users\mtoro\AppData\Local\AI-Make\fusion-mcp-0.7.0-review\server.py`.
- Resolved physical 0.7 tree: `C:\Users\mtoro\AppData\Local\packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\AI-Make\fusion-mcp-0.7.0-review`.
- Candidate package root: `C:\Users\mtoro\OneDrive\Documents\ChatGPT\AI Make Fusion MCP\candidate-review\ai-make-fusion-MCP\software\fusion-prompt-mcp`.
- Shared queue: `C:\Users\mtoro\.fusion-prompt-mcp`.
- Default Autodesk add-in junction points to a retained **0.6.0** add-in, while a separate `FusionBridgeInstallation` is **0.4.1**. Neither is evidence of a loaded bridge. Do not copy over or retarget those folders/junctions.

Use the candidate in its current folder; no pip/setup helper, copy into an installed folder,
or source patch application is part of this procedure. Keep source fixed during the session
and verify `candidate-review/LOCAL-SOURCE-SHA256.json` before activation. This folder is under
OneDrive; finish file hydration/sync first and abort if files change during validation.

1. **Preflight and freeze producers.** Pause this Fusion MCP in every connected client/session;
   existing Python process pairs are MCP clients, not proof of multiple native bridges. Recheck
   request/processing files and queued/waiting/running jobs read-only; stop on any unresolved live
   operation. Preserve terminal failures/interrupted jobs and original operation IDs; do not replay
   or cancel them to obtain a clean result. If Fusion is open, inspect owner work without opening
   K1/Reward Rocket. Do not close dirty documents or save production work without the owner's
   direction. Run `examples/native_runtime_probe` from Fusion's Scripts tab to retain actual
   module paths/versions before switching; its candidate gate may correctly report blocked for
   0.7. If no Fusion process exists, record that no loaded baseline can be observed.
2. **Back up at a safe stopped boundary.** Stop all FusionPromptBridge entries in every Fusion
   instance and exit Fusion only when owner work is safe. Stop/disconnect all clients for this
   MCP. Back up the config and its exact fusion table, current registration/startup flags, the
   actual loaded source if observed, and the full runtime directory into a timestamped private
   local backup outside the source tree. Use SQLite's backup API for `jobs.sqlite3` (or a fully
   quiescent copy including any WAL/SHM); retain artifacts/reports/checkpoints. Do not delete a
   lock file or reset the database. Record backup hashes and old source hashes.
3. **Switch this MCP entry only.** Retain the existing `command` above. Set its `args` to the
   single exact string:
   `C:\Users\mtoro\OneDrive\Documents\ChatGPT\AI Make Fusion MCP\candidate-review\ai-make-fusion-MCP\software\fusion-prompt-mcp\server.py`.
   Do not alter fusion_geometry, other MCPs, model settings or AI_MAKE. Reconnect only one test
   client after the candidate bridge is running. No producer may submit work while native
   fixture scripts are running.
4. **Activate exactly one bridge in a fresh Fusion process.** In Scripts and Add-Ins, disable
   startup on all old FusionPromptBridge entries, add the candidate root's `FusionPromptBridge`
   folder, leave candidate Run on Startup off, and Run it once. Do not use the default 0.6 junction
   or the 0.4.1 folder. Restarting only the add-in is insufficient to exclude cached Python modules;
   use a fresh Fusion process. If a queue-owner lock error occurs, stop and identify its owner;
   never remove/bypass the lock or start a second bridge. Startup can mark prior live jobs
   interrupted, so step 1 must be repeated immediately before starting it.
5. **Verify identity before creating fixtures.** Run the read-only `examples/native_runtime_probe`
   script from this candidate root, retain its `runtime.json`, and require status pass with every
   loaded bridge module rooted in this candidate, one live worker/open queue lock handle, idle
   bridge, and actual Fusion/embedded Python versions. Confirm the client exposes 32 tools and
   native `fusion_capabilities` reports 0.8.0 / caller 2.0 / rules 1.3.0. Retrieve rules and verify
   SHA256 `d01f958cedf8f435c348dbd10185635c75f4e1205985a6dc5d5cf78bc4e3ba79`.
   A blank disposable design may be created for capability calls if Fusion requires one; never
   activate a production model to satisfy this check. Abort on any path/version mismatch.
6. **Run only the prepared disposable fixtures.** Register/run `examples/native_engineering_fixtures`
   and `examples/native_k1_contract` from this candidate root as Scripts. They each create a new
   unsaved fixture; neither opens or cloud-saves production CAD. Retain every temp result folder,
   including SQLite/events, native JSON, STEP and PNG evidence or errors. Verify defect negatives,
   seam positive, recovered reference/protected comparison and no-replay recovery manually;
   `all_declared_defect_cases_matched` alone does not cover recovery. For K1, inspect all case
   rows, owned parameters/boundary report, STEP receipt and independent presentation/restoration
   observations. Preserve failed/partial fixture documents for diagnosis. Do not replay a failed
   fixture job; any authorized rerun gets a new disposable document and result directory.
7. **End the session with rollback below**, even if both runners pass. Report actual observations
   per case and separate direct fixture/API behavior from MCP-native dispatch coverage. The
   isolated STDIO test has already passed but does not prove client-to-native dispatch. Cloud
   first-save, long Boolean/cancel, kept tools, finite ligaments and manufacturing/slicer/physical
   gates remain unqualified; none is added to this temporary session.

**Rollback for this session:** stop candidate work at a cooperative idle boundary; retain all new
jobs/events/reports and native fixture outputs. Stop candidate bridge and test client; leave
candidate startup disabled. Exit Fusion safely to clear module caches. Restore only the saved
fusion config table and activate exactly one bridge from the retained matching **0.7 review**
root (`...\fusion-mcp-0.7.0-review\FusionPromptBridge`) in a fresh Fusion process. Keep other
legacy entries disabled so the 0.6 junction cannot become an accidental second owner. Restore
the prior observed 0.7 startup preference if one was established; otherwise leave it manual.
Verify actual loaded 0.7 module paths and native 0.7 / caller 1.1 / rules 1.2.0; use a 0.7 caller
shape. If the observed preflight source differs from configured 0.7, stop and review that mismatch
before switching rather than inventing a baseline. Keep the updated runtime DB and artifacts in
place; never restore the old DB over new history or rewind CAD/cloud state. A newly blocked
0.8 authoring claim must not be continued with 0.7 to bypass its ledger. Preserve both backups
and unresolved work if rollback identity cannot be demonstrated.

**Approval requested only after preparation:** authorize this one temporary candidate activation,
two disposable fixture runs, evidence retention and rollback to the verified 0.7 baseline? No
approval has been received or inferred. No installation/activation/config edit has been executed.

## Original archive release procedure (historical preparation)

**Do not install or push this candidate yet.** The K1 brief supersedes the Oct 20 installation
permission for this new work. Release requires project completion AND Mauricio's approval of
the printed design. Neither is established by the supplied evidence. No production model,
installed bridge, printer, preset, recording or physical job was changed in this implementation.

## Review now

Baseline: workbench `6db17f97543ab88857f185343df5b02484f9e421`.
The review archive contains the candidate source snapshot, forward/reverse patches, file hashes,
software results and these instructions. It excludes the private evidence bundle, CAD, runtime
SQLite databases, print files, credentials and host configuration. Keep ledger on workbench.

In a separate checkout, preserve existing edits and compare HEAD to the baseline before applying
a patch. `git apply --check changes.patch` must succeed; inspect conflicts rather than replacing
newer files. Never copy the old 0.7 ZIP over newer work. Source tests:

```powershell
Set-Location C:\AI-Make\fusion-mcp-0.8-review\software\fusion-prompt-mcp
& $Python -m unittest discover -s tests -v
& $Python tests\check_mcp.py
& $Python tests\benchmark_responses.py
```

Set `$Python` to the **existing** environment's python.exe. No dependency install is needed if
it already has the supported MCP SDK. `check_mcp.py` creates an isolated journal and never
contacts Fusion. It was not run here because the SDK is absent and installation is prohibited.
The native fixtures also remain unrun here. API-double success does not replace either gate.

## After the stated release condition and explicit deployment approval

1. Inspect outstanding jobs and unsaved owner work with the currently installed bridge. Reconcile
   uncertain operations, preserve actual completed stages, and save only as authorized. Do not
   close/reload dirty work or restart in the middle of a native operation.
2. Back up the current installation and the specific MCP configuration entry. Preserve the full
   current runtime directory, including reports/artifacts and a consistent SQLite backup (stop
   bridge/client first, or use SQLite backup API; do not copy a live DB without its WAL).
3. Stage this candidate in a **new** folder. Retain the working 0.7 folder/environment. Point only
   this MCP's configuration entry to the staged `server.py`; no other client/model settings.
4. Stop the old add-in, register the candidate `FusionPromptBridge` folder and restart/reconnect
   the two processes safely. Verify loaded runtime 0.8.0, caller 2.0, rules 1.3.0/hash, 32 tools,
   and the actual module paths. Changed files alone do not prove a loaded update.
5. Run real isolated STDIO and both native runners only in newly created disposable documents:
   `examples/native_engineering_fixtures` and `examples/native_k1_contract`. Preserve every JSON
   result, including failures. Never use the K1 or Reward Rocket assembly as a fixture.
6. First-save metadata/cloud identity needs a separately authorized disposable project/version
   test. Verify one save/version and uncertain reconciliation; no replay. M07–M11 remain deferred
   and must not be advertised as qualified by these runners.

## Rollback

Stop candidate work at a safe boundary, retain its latest jobs/events/reports/checkpoints and
actual CAD/cloud versions. Restore only the prior MCP config entry and activate the retained
0.7 add-in/environment. Do not restore an old runtime DB over current history or rewind geometry.
The additive SQLite tables can remain, but 0.7 does not enforce the new authoring ledger: do not
continue blocked work merely by switching versions. Compact callers need the 0.7 output adapter
or must switch with the server version. Reverse patches are for an isolated clean source checkout,
not an automatic production rollback. Recheck loaded path/version afterward.
