# Current state

Branch: workbench. Version: v0.4.1 development; modeling rules version 1.0.3.

## Now

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

80 automated tests pass (including 17 hygiene regressions); real STDIO MCP checks pass with
25 tools and the modeling-rules resource. These include API doubles, not native Fusion execution.
Reported by Mauricio: v0.4 is running in local Fusion. No result of the requested read-only smoke
test was supplied. No v0.4.1 live geometry, audit or export validation occurred here.

## Next question

After updating both installed processes to v0.4.1, can the client retrieve the rules and audit a
copy without changing it? Confirm under-constrained fixture blocks checked export and recovery
checkpoint remains available; follow docs/modeling-hygiene.md live acceptance.

## Files touched

Rules/source docs, AGENTS and installed guidance, MCP server/dispatcher/resource, hygiene inspector,
batch helpers, capability/version metadata, regression/protocol tests and working-state records.

## Open gates

Live Fusion acceptance; manual review of non-automatable rules; remaining verification roadmap;
license/public release. No challenge clock, budget or physical outcome inferred.
