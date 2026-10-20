# v0.7 development: installation and rollback

Reviewed package baseline: workbench c0f7857cfcd38ef3e0c834a7ed1bfab323a8749c. Source adoption and local installation are separate states; see CURRENT.md. Existing dependency requirements unchanged. Do not overwrite newer source. Runtime 0.7.0 / caller contract 1.1 / rules 1.2.0 / 32 tools; scope/task remain 1.0.

## Adopt the committed source without replaying its patch

Mauricio authorized implementation and installation on 20 October 2026. Source is
being adopted on `workbench`; actual local application/reload remains pending from
this session. This authorization does not permit discarding unsaved designs,
resetting local source changes or touching completed product models.

Use the current committed 0.7 source from a clean staging checkout. Inspect the
actual local Git status and effective MCP command/add-in path first. Do not run
`git reset --hard`, force-pull, or apply the old forward patch a second time.
Preserve local changes and reconcile only real conflicts. The original review
archive/patch remains provenance, not an instruction to downgrade newer source.

## Install in the existing local environment

1. Stop submitting jobs. Inspect pending/failed/interrupted jobs; reconcile uncertain cloud saves and preserve human edits. Wait for active operations. Do not delete the journal to bypass a blocker.
2. Stop the MCP client and FusionPromptBridge. Close Fusion normally after resolving unsaved-document prompts. Do not interrupt uploads. Restarting both processes is needed to clear imported Python modules.
3. Back up the existing installation, effective MCP configuration and runtime with the processes stopped. Use the actual discovered paths; the following historical path is an example. Point `$Source` to `software\fusion-prompt-mcp` in the staging checkout:

```powershell
$ErrorActionPreference = 'Stop'
$Install = 'C:\AI-Make\fusion-prompt-mcp'
$Checkout = 'C:\AI-Make\staging\ai-make-fusion-MCP'
$Source = Join-Path $Checkout 'software\fusion-prompt-mcp'
$Backup = "C:\AI-Make\backups\fusion-prompt-mcp-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$Runtime = Join-Path $env:USERPROFILE '.fusion-prompt-mcp'
if (!(Test-Path (Join-Path $Source 'FusionPromptBridge\engineering.py'))) { throw 'Incorrect package path' }
if (!(Test-Path (Join-Path $Install 'server.py'))) { throw 'Existing installation not found' }
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
Copy-Item -LiteralPath $Install -Destination (Join-Path $Backup 'installation') -Recurse
if (Test-Path $Runtime) { Copy-Item -LiteralPath $Runtime -Destination (Join-Path $Backup 'runtime') -Recurse }
Copy-Item -Path (Join-Path $Source '*') -Destination $Install -Recurse -Force
Write-Host "Backup: $Backup"
```

Before copying, reconcile locally customized tracked source rather than overwriting it blindly. Preserve a backup of the effective client configuration even though this upgrade does not need to edit it. If Fusion points to a separate registered add-in copy, update that copy from the same source and verify both paths. Never replace `~/.codex/config.toml` or change its providers/models/permissions.

Copy the complete source including engineering.py, engineering_geometry.py, recovery.py, manufacturing.py, job_store.py, server.py and installed modeling-rules.md. The package contains no virtual environment, runtime journal or machine config. Keep the existing `.venv` and MCP configuration. Do not run setup-windows.ps1 or install dependencies for this upgrade.

4. With the existing `.venv\Scripts\python.exe`, run `tests/check_mcp.py`; it uses an isolated temporary journal and does not connect to Fusion. Record the actual result. Launch Fusion, start the existing add-in from this installation and reconnect the MCP client. Retrieve capabilities and rules: expect 0.7.0, caller 1.1, rules 1.2.0, engineering plan 1.0, 32 tools. Stop if versions differ.
5. Keep v0.6 writer/scope/pin requirements. Opt into the new engineering plan; it is not automatically applied to old scripts. Complete the isolated native acceptance in engineering-validation.md before using this candidate for important work. Installation and a disposable native check are covered by the current request; they have not run from this chat. Use only the disposable fixture, preserve other documents and report its actual pass/fail/unproven results. Do not treat the completion dialog as a passing result. If a GUI restart/action is unavailable to local Codex, request only that exact action and keep a resumable handoff.

## Rollback software

Stop both processes and preserve the current runtime journal and all newer CAD/cloud versions. v0.6 does not understand the new helpers or detailed-result selector. Resolve/cancel queued v0.7 jobs and update callers before downgrading. Software rollback does not roll back geometry.

```powershell
$Install = 'C:\AI-Make\fusion-prompt-mcp'
$Backup = 'C:\AI-Make\backups\fusion-prompt-mcp-REPLACE_WITH_ACTUAL_STAMP'
$SavedInstall = Join-Path $Backup 'installation'
if (!(Test-Path (Join-Path $SavedInstall 'server.py'))) { throw 'Backup not found' }
$Quarantine = "$Install-v07-held-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Move-Item -LiteralPath $Install -Destination $Quarantine
Copy-Item -LiteralPath $SavedInstall -Destination $Install -Recurse
```

Retain the quarantined installation and current `%USERPROFILE%\.fusion-prompt-mcp`. Never overwrite the current jobs database with the old backup: doing so can discard duplicate-prevention/recovery evidence. Restart and verify v0.6 versions before using its compatible callers. Inspect specific checkpoints/cloud versions before any CAD restoration; no restore is automated.

For historical review-package use only, source rollback on an unchanged patched checkout: `git apply --check fusion-mcp-v0.7.0-rollback.patch`, then `git apply fusion-mcp-v0.7.0-rollback.patch`. Stop on conflicts and preserve newer work. Patch round-trip validation is recorded separately from Windows installation testing.
