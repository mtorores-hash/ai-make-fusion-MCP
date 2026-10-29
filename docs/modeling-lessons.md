# Modeling and verification lessons

Reusable requirements distilled from supplied feedback. Original source and reported project
results remain in Git history at `b193554700bf5da56ba9e05df562dc5426dd9fc0`.
See [coverage and remaining work](upgrade-v0.4.md). This roadmap does not imply implementation
or live Fusion validation of every capability.

## Execution and motion

Regenerate after geometry edits and before dependent measurements; omit regeneration for
read-only queries. Bound synchronization and never expose an unchecked fast mode. Verify joint
values AND independently expected world transforms before measurements, restoring poses on error.
Use conservative collision filtering and adaptive sampling; report unresolved intervals. Finite
samples cannot prove continuous clearance. Cache only with reliable revision invalidation;
distinguish shape edits from rigid motion. Profile solve, measurement, export and checkpoint time.

Acceptance: queries avoid full regeneration; a narrow-collision fixture verifies transforms,
refines samples and restores its initial pose on error.

## Geometry experiments

Run risky edits on checkpointed disposable copies. Compare body count, solid validity, volume,
envelope, protected interfaces and feature health with matching before/after views. Healthy
features alone do not establish acceptable geometry. Reject destructive candidates and preserve
the source; rejected candidates must not become release artifacts.

Acceptance: a destructive edit fails explicit geometry guards.

## Surface and print review

Locate short edges, slender faces, thin regions, near-coincident surfaces and narrow protrusions
with units and thresholds. Assess positional, tangent and curvature continuity. Small faces are
review candidates, not automatic defects. Preserve intentional shoulders, lands, seals and datums.

Print checks require orientation, nozzle width and layer height. Check isolated layer starts,
cantilevers, bridge support at both ends, thin walls, support-removal paths and mesh integrity.
Distinguish predicted geometry, actual slicer outputs and physical performance.

Acceptance fixtures: floating island, supported bridge, unsupported cantilever, thin lip and
legitimate retaining shoulder.

## Tolerances and assembly access

Define functional interfaces with independent signed dimensional bounds and provenance. Separate
radial, diametral and axial clearance; account for alignment, backlash, print variation and
hardware uncertainty. Report nominal/worst-case margins and controlling assumptions. Provisional
hardware dimensions cannot establish verified fit.

Check nut/washer insertion, clip removal, bearing-stack assembly and driver access at the correct
assembly step. Distinguish intentional contact, heat-set fits, stops and forbidden overlaps.
Include a nominally clear but tolerance-failing fixture.

## Parametric authoring

Prefer coherent profiles and junctions over accumulated local repairs. Reusable fastener stacks,
bosses, pockets, spring cups, gussets and lofts need explicit hardware inputs. Parameters must
drive native geometry. Select by semantic role, feature lineage and geometric predicates;
re-resolve after edits and reject ambiguity instead of trusting edge indices or token strings.

Acceptance: independent parameter changes update geometry, expose failed requirements and
preserve protected interfaces.

## Calculations and deliverables

Record materials, uncertainty, print orientation, directional strength, safety factors, spring
properties and loads. Tie calculations to a geometry fingerprint and label simplified models;
nominal geometry cannot certify creep or hardware pullout.

Tie CAD, STEP, oriented STL, BOM, manual, checks and images to one revision. Reject stale files
and calculations; invalidate affected results after edits. Check units, mesh closure, export/source
bounds and volume; reopen archives and verify parts/joints. Hash consistency alone is not
engineering validation.

## Repeatable review and evidence

Save camera, visibility, style and output dimensions for honest comparisons. Use reproducible
frames for exploded assemblies and motion; rendered animation is not a physical test.
Preserve transport/API-double tests and add live Windows/Fusion fixtures with versions, expected
measurements and tolerances. Use synthetic hardware where redistribution is restricted.
Keep reported, automated, native-kernel and physical evidence distinct.
