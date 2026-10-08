# Current state

Branch: workbench. Version: v0.5.0 development; modeling rules version 1.0.5.

## Now

2026-10-08: implemented Fusion cloud project/folder creation, named native part/version saves,
opening, linked insertion and selected reference updates. Added single-use pre-edit tokens and
clean cloud-version manifests for linked checkpoints. 28 MCP tools; user edits and existing
assembly links are preserved. Cloud copy is not automatic assembly/joint migration.


2026-10-08: rules 1.0.4 require connection selection before hardware, a short rationale per
distinct connection and final fastener/access review. Manual guidance, not automatic optimization.

2026-10-08: rules 1.0.3 require complete intended junctions, local width/thickness checks,
intentional surface continuity and revision-specific close-up/section evidence before completion.
Added manual audit reminder; no automatic junction-geometry validator is claimed.

2026-10-07: rules 1.0.2 default to simple PCB connector/pin clearance volumes and cable
routes to the correct board area/orientation. Detail is opt-in; supplier CAD originals preserved.
Rules copy/version/loader and Python syntax checks pass; no new live Fusion validation.

2026-09-27: rules 1.0.1 require commercial-hardware CAD sourcing before reconstruction or
placeholders. Served rules and audit manual-review checklist updated; runtime stays v0.4.1.

2026-09-27: working documentation and spring-cup example generalized; project anecdotes removed
from the lessons summary. Runtime behavior and version remain v0.4.1. Original source is in Git history.

Mauricio supplied a parametric modeling standard. Original preserved in
docs/Fusion-Parametric-Modeling-Best-Practices.md; operational rules shipped with the software,
linked from AGENTS, and exposed by MCP tool/resource. Added read-only whole-design hygiene audit
and explicit checked-export gate. Existing checkpoints/working exports are not blocked.
Prior verification roadmap coverage remains in docs/upgrade-v0.4.md; this update does not complete it.

## Last experiment / evidence

106 automated tests pass (API doubles, numerical and filesystem tests). Real STDIO MCP
initialize/list/schema/rules/resource/job checks pass with 28 tools using Python 3.12 and MCP
1.30.0. Tests cover user-edit rejection, version conflicts, pending/completed saves, duplicate
requests, restart interruption, component-copy futures and selective reference updates.
No live Fusion cloud/kernel test or installation on Mauricio's PC performed here.

## Next question

Upgrade BOTH local server/add-in to v0.5.0 and retrieve rules 1.0.5. Run the disposable-project
acceptance in docs/cloud-workflow.md: manually edit/save a named part, update its assembly
reference, inspect placements/joints, save and resume AI work without discarding the edit.

## Files touched

Cloud module, dispatcher, job store, server schemas, batch checkpoints, experiment boundary,
versions/rules, tests, install/workflow/reference docs and working-state records.

## Open gates

Live Fusion cloud and geometry acceptance; no distributed locking or arbitrary-Python sandbox;
existing-component linkage migration remains deliberate work; license/public release.
No challenge clock, budget, physical outcome or installed-PC update inferred.
