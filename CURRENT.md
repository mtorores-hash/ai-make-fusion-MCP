# Current state

Updated: 2026-09-23. Branch: workbench. Version: v0.4.0 development.

## Now

Implemented the first BRANCA execution/verification slice. See docs/upgrade-v0.4.md for exact
coverage and the outstanding P1/P2 work. Canonical requirements preserved in docs/branca-lessons.md.
The Windows installation is not changed by this hosted repository update.

## Last experiment / evidence

63 automated tests pass (numerical/filesystem tests and Fusion API doubles); real STDIO MCP
protocol checks pass with 23 tools. No live Fusion/kernel or physical printing test ran here.
Reported BRANCA run: 1,233 native interference checks across 56 verified poses, archive reopening
with four printed solids and 11 joints, and four parts sliced. These are user-reported v0.3/custom-script
workflow results; underlying JSON evidence was not attached, and they do not validate v0.4 wrappers.

## Next question

Does v0.4 complete disposable F3D import/close and joint/world-transform verification on a copy
in Windows Fusion? Run docs/validation.md acceptance gates before relying on these native paths.
Then implement remaining print/surface audits, path/contact policies and authoring/release/media layer.

## Files touched

Batch runner, queue validation, geometry checking, new policy/experiment/intent modules,
regression tests, motion example, documentation and this working ledger.

## Open gates

Live Windows/Fusion acceptance; remaining roadmap; license/public-release decision.
No public release, challenge clock, budget or physical outcome inferred.
