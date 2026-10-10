# v0.6.0 development upgrade and rollback

**Source push to workbench approved on 2026-10-10. Installation, restart and native acceptance remain unperformed and require separate approval.** Base: workbench `b15d491fe87fd4b1a1953ea148378f045f621f14`; server/add-in 0.6.0, rules 1.1.0, contract 1.0, 32 tools. Dependencies unchanged (`mcp>=1.12,<2`, Python 3.10+). No dependency was installed during development.

## Repository source and the earlier review patch

Current `workbench` already contains this update; do not apply the earlier review patch again.
The following patch instructions are only for a checkout still at the pre-update baseline.
Use a clean local checkout of the target repository. Inspect `git status` and the current workbench head; preserve newer commits. The package includes a full updated `source` tree and `fusion-mcp-v0.6.0.patch`. A patch is preferable to replacing a newer checkout.

```powershell
git switch -c review/fusion-workflow-v0.6 workbench
git apply --check C:\path\to\package\fusion-mcp-v0.6.0.patch
git apply C:\path\to\package\fusion-mcp-v0.6.0.patch
git diff --check
```

If the preflight fails because workbench advanced or local files differ, stop and reconcile those changes; do not reset or overwrite them. The package's baseline record identifies the upstream SHA; the synthetic local snapshot commit is not an upstream commit. No push/merge command is part of this procedure.

## Upgrade both local processes after approval

1. Inspect every pending/failed/interrupted cloud job and Fusion's version history. Preserve outstanding human edits through an explicitly chosen save. Resolve uncertain uploads before changing versions. Stop submitting tasks; wait for active jobs. Do not delete `jobs.sqlite3` or its artifacts to clear a blocked operation.
2. Stop the Fusion MCP client connection and stop FusionPromptBridge in Fusion Scripts and Add-Ins. Close Fusion normally after resolving unsaved-document prompts. This clears imported add-in modules; do not terminate it during uploads.
3. Extract the reviewed package to a staging folder. If using a GitHub workbench ZIP instead, set `$Source` directly to its extracted `software\fusion-prompt-mcp` folder; its layout does not contain the review package's `source` directory. In PowerShell set the paths below; `$Package` contains `source`, patch and top-level instructions. Back up the complete existing installation **and** the runtime directory with both processes stopped.

```powershell
$ErrorActionPreference = 'Stop'
$Install = 'C:\AI-Make\fusion-prompt-mcp'
$Package = 'C:\AI-Make\staging\Fusion-MCP-v0.6.0-review'
$Source = Join-Path $Package 'source\software\fusion-prompt-mcp'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Backup = "C:\AI-Make\backups\fusion-prompt-mcp-$Stamp"
$Runtime = Join-Path $env:USERPROFILE '.fusion-prompt-mcp'
if (!(Test-Path (Join-Path $Source 'FusionPromptBridge\scope.py'))) { throw 'Wrong package source path' }
if (!(Test-Path (Join-Path $Install 'server.py'))) { throw 'Existing installation not found; do not treat this as a fresh install' }
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
Copy-Item -LiteralPath $Install -Destination (Join-Path $Backup 'installation') -Recurse
if (Test-Path $Runtime) { Copy-Item -LiteralPath $Runtime -Destination (Join-Path $Backup 'runtime') -Recurse }
Copy-Item -Path (Join-Path $Source '*') -Destination $Install -Recurse -Force
Write-Host "Backup: $Backup"
```

The reviewed source snapshot contains no `.venv`, job database or personal config, so the copy preserves the existing environment/config. Copy **all** add-in modules, including new `scope.py`, `retirement.py`, `authoring.py`, and the rules beside `server.py`. Do not run `setup-windows.ps1` for this upgrade; no dependency change is required.

4. Keep the existing MCP command `C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe` and argument `C:\AI-Make\fusion-prompt-mcp\server.py`. If dependencies are missing, stop and obtain approval for any separate installation.
5. Start Fusion, load the existing add-in from this same location, then reconnect the MCP client. Retrieve capabilities, list tools and rules: runtime **0.6.0**, caller contract **1.0**, rules **1.1.0**, **32** tools. A mismatch means one process still uses old files; stop work and correct it.
6. Migrate token callers: observe with `inspect_document_state`; acquire with `acquire_edit_token`, matching writer/pins on requests. Use explicit scoped contract for checked deliverables. Legacy clients must request `acquire_token=True` and have no new bounded-edit guarantee.
7. Run the separately approved [disposable acceptance](disposable-acceptance-v0.6.md). API doubles and syntax checks do not qualify the installed build for important models.

## Rollback software after approval

Stop both processes as above. Preserve the **current** runtime journal and any models/cloud versions created since upgrade; software rollback is not CAD rollback. Confirm uncertain operations in v0.6 before downgrading: v0.5 does not enforce the new uncertainty block or scope/task semantics.

```powershell
$Install = 'C:\AI-Make\fusion-prompt-mcp'
$Backup = 'C:\AI-Make\backups\fusion-prompt-mcp-REPLACE_WITH_ACTUAL_STAMP'
$SavedInstall = Join-Path $Backup 'installation'
if (!(Test-Path (Join-Path $SavedInstall 'server.py'))) { throw 'Backup not found' }
$Quarantine = "$Install-v06-held-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Move-Item -LiteralPath $Install -Destination $Quarantine
Copy-Item -LiteralPath $SavedInstall -Destination $Install -Recurse
```

Keep the quarantined directory and current `%USERPROFILE%\.fusion-prompt-mcp`. **Do not restore an older jobs database over the current journal**: that could erase deduplication and late-save evidence. Restart both processes; verify the previous runtime/rules/tool count and resume only with its compatible callers. New v0.6 queued requests must not be executed by v0.5; cancel/inspect them before switching. Old server code may not understand current result fields. No native/cloud rollback is automated; recover specific versions/checkpoints only after inspecting their contents and links.

For source rollback on an unchanged patched checkout, use `git apply --check fusion-mcp-v0.6.0-rollback.patch` then `git apply fusion-mcp-v0.6.0-rollback.patch`. It reverses only this change set. Stop on conflicts; preserve newer work. Both patch directions are tested against the packaged baseline/update tree.
