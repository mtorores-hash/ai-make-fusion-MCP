# Reward Rocket lessons: current-state gap analysis

Inspected current workbench c0f7857cfcd38ef3e0c834a7ed1bfab323a8749c before editing (not the older installed snapshot). Original 150 tests passed unchanged. The completed product's reported 15-delivery test is user evidence about that product, not qualification of this MCP change. No Reward Rocket file was opened.

| Area | Existing at baseline | Gap | Bounded v0.7 change |
| --- | --- | --- | --- |
| Interfaces | Geometry tags, dimensional budgets, protected snapshots, scoped caller evidence | No shared revision-bound interface/envelope declaration | Interface map with geometry/datums, provenance, uncertainty, dimensions, mating direction, parameter dependencies, protected metrics and access envelopes |
| Geometric quality | Short-edge/small-face/slender-face review candidates; native health; interference/distance | No declared planar-wall step or sampled smoothness check | Declared planar continuity, gap interval, overlap allowance, sampled tangent-plane/curvature rejection; exact refs, values, limits and locations |
| Assembly access | Static interference, finite joint sampling | No named assembly-operation envelopes | Conservative world-space boxes translated through explicit poses against declared solid obstacles; per-pose overlap evidence |
| Reference recovery | Tokens, selectors, feature-origin tags; durable operation IDs/checkpoints | No signature fallback or staged mutation reconciliation | Optional signature-bounded feature fallback; ambiguity/error codes; persisted stage boundaries, before/after observations and protected rechecks |
| Efficient evidence | Selected scopes, geometry fingerprints, paginated inspection | No shared engineering report cache/compact summary | Check-specific fingerprints of resolved refs, body revisions, placements, declared datums/parameters and requirements; detailed artifact retrieval, timings and counters |
| Manufacturing | Revision/hash release manifest, print-copy export | Missing linked print/bed/support/interface declaration | Generation-time native source identity plus revision/byte-matched manufacturing declaration; explicit unproven slicer readiness |

## Deliberate limits

This is an additive batch-helper extension, not seven new MCP tools. Tool count remains 32. Existing surface audit, clearance budget, interference, checkpoints, scoped validation and release manifest are reused or extended.

Not implemented: automatic interpretation of arbitrary contour intent; global near-coincident/minimum-wall detection; general junction completeness; continuous swept-volume collision proof; rotating envelopes; automatic dependency graph discovery; automatic shape repair; full G2 proof; aesthetic approval; automatic overhang/bridge detection or slicer settings. Declared pairs and paths cover the bounded high-value cases without pretending to solve these broader problems.

Native fixtures are provided but unrun because no Fusion connection was available. API doubles establish behavior and reporting, not native geometry correctness or production readiness. See engineering-validation.md for measured evidence and limits.
