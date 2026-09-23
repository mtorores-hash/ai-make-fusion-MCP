# BRANCA lessons supplied for MCP development

Received 2026-09-23 in this session. The text below is preserved from the attachment.
Observations and numerical results are user-supplied reports; referenced BRANCA JSON evidence
was not attached or independently inspected in this update. The text begins at P1; any earlier
P0 section is unavailable. Implementation coverage: [v0.4 update](upgrade-v0.4.md).

## P1 - Faster execution with evidence that the model actually changed

Observed: the runner calls computeAll after every batch, including inspection/capture batches; the existing motion helper calls it at each pose. This added substantial overhead. Our final native sweep explicitly verified occurrence transforms rather than trusting the requested joint value alone.

Add a documented recompute policy: required after geometry changes, deferred within a safe modeling batch, and omitted for genuinely read-only operations. Do not expose a silent unchecked fast mode. Provide a supported bounded solver/event synchronization helper. Motion sampling should check requested pose, joint value AND world transform before measuring. Cache immutable shape information by model revision, invalidate it after edits, and separate shape changes from rigid pose changes.

Use conservative bounding-volume filtering before expensive intersection checks. Adaptively refine near contact and report unresolved intervals. A finite sample sweep is not continuous collision proof. Profile solve, measurement, export and checkpoint time separately.

Acceptance: repeated read-only inspection performs no full regeneration. Motion fixture reaches verified poses, restores the original pose on error, and detects a deliberately narrow collision interval when refinement is enabled. Report the limits of any sampling guarantee.

## P1 - Safer geometry experiments

Observed: some fillet/heal attempts failed, one radically changed body volume, and outward reinforcement improved the structural calculation but created unacceptable exterior lips.

Add try_feature / experiment helpers that operate on a checkpointed disposable copy, with explicit acceptance rules: expected body count, solid validity, maximum volume and envelope change, protected bores/datum faces, feature health and before/after captures. Rejected candidates must never become release artifacts. Discarding an experimental document is safer than assuming deleteMe reverses every consequence of arbitrary Python.

Expose a measured before/after geometry delta. Do not declare the result good merely because a feature reports healthy.

Acceptance: a deliberately destructive face-heal candidate is rejected by volume/body guards, and the accepted source remains available. The report shows exactly why the candidate was rejected.

## P1 - Surface quality and manufacturing audit

Observed: valid single solids and closed meshes still contained visually abrupt intersections, slender lips and an internal fillet remnant that started as an unsupported printed island. Those required separate visual and layer checks.

Add a surface audit that flags short edges, slender faces, thin regions, near-coincident surfaces and narrow protrusions. Sample neighboring surface normals and curvature to characterize positional, tangent and curvature continuity. Show location, units, thresholds and diagnostic views. Small faces are candidates for review, not automatic defects.

Let designs mark intentional functional edges: washer lands, retaining shoulders, sealing surfaces, datums and bores. Do not round them automatically.

Add a print audit driven by explicit orientation, nozzle width and layer height: isolated layer starts, cantilevers, bridge support at both ends, thin walls, enclosed support-removal paths, supported versus clean geometry and mesh integrity. Bridge length and overhang angle alone are insufficient. Export actual slicer review artifacts through a separate adapter; distinguish predicted geometry from physical print performance.

Acceptance: synthetic fixtures for a tiny floating island, a valid two-ended bridge, an unsupported cantilever, a thin lip and a legitimate retaining shoulder. Detect and locate the defects without treating all small/curved boundaries as failures.

## P1 - Tolerance-aware mechanisms and assembly access

Observed: zero nominal interference did not settle whether washers, nuts, collet clips and tools could be inserted or removed. Adjustable bearing preload was needed to avoid clamping through a printed roof. The tightest measured arm/button-head gap was 0.35 mm; a separate stack calculation left 0.05 mm under its stated conditions.

Add named functional interfaces with directional, independent dimensional bounds: printed surfaces, hardware size, center location, angular misalignment and fit allowance. Distinguish radial, diametral and axial clearance; include backlash and alignment separately. Report nominal and worst-case margins and which assumptions control them.

Extend motion sampling into insertion/removal/tool-access paths with prerequisite assembly steps. Support intentional contact, interference fits for heat setting, stops, and forbidden overlaps as different categories. Keep provenance and measurement status for purchased hardware; provisional collet dimensions must not become certified fit automatically.

Acceptance: insert a nut and washer through a side opening, remove a clip with tubing installed, insert the bearing stack into the loose arm, and verify driver access at the specified assembly step. Include a nominally clear but tolerance-failing fixture.

## P2 - Better tools for creating a coherent design from scratch

Lesson about modeling strategy: repeated local repair features accumulated complexity. Rebuilding a common profile or junction earlier would often have been cleaner. This is partly a modeling decision, not a transport defect.

Add reusable, tested primitives for fastener stacks, heat-set bosses, side-loading nut/washer pockets, guided spring cups, rounded gussets and connected lofts. Hardware dimensions and supplier-specific cavities must remain explicit inputs. Parameters should drive real sketches/features, not exist as unused labels.

Support semantic tags such as spring_axis, motor_datum, washer_seat and protected_collet_shoulder, linked to native feature lineage and geometric predicates. After edits, re-resolve and reject ambiguous matches rather than trusting face indices or token-string equality. Store design requirements with links to the geometry and checks that satisfy them.

Acceptance: change spring length, washer thickness and motor spacing independently. Geometry updates, failed requirements become visible, protected interfaces stay intact, and no stale hard-coded face indices are required.

## P2 - Engineering calculations and synchronized release packages

Keep calculation models explicit and auditable. Store material values, uncertainty, print orientation, XY/Z strength assumptions, safety factor, spring dimensions/rate, load cases and physical limits. Tie calculations to a geometry fingerprint. Simplified section calculations must be labeled as such; hardware pullout and printed creep cannot be certified from nominal geometry.

Add a release manifest tying F3D, STEP, bed-oriented STL, supported alternatives, BOM, manual, checks and images to one revision. Geometry changes invalidate affected checks, documentation and videos. Validate units, mesh closure, export/source bounds and volume with appropriate numerical tolerances; reopen the F3D and verify parts/joints.

Acceptance: deliberately mix an older STL or calculation into a new package and have release validation reject it. Emit hashes and the model revision used for every result.

## P2 - Repeatable visual review and presentation

Extend the existing camera/capture helpers into saved review scenes: named cameras, visible-edge/shaded pairs, isolated components, clipped sections where supported, and suppression of sketches, construction geometry, joint glyphs and selections. Preserve camera and visibility metadata so comparisons are honest. Allow annotated defect positions.

For AI Make, add a deterministic timeline for exploded assembly and joint motion, fixed 1920x1080 or higher output, frame rate, holds and reproducible frame metadata. Encoding can live in an external presentation layer. A rendered animation is not evidence that the physical mechanism was tested.

Acceptance: render before and after with identical camera/visibility; assert actual output dimensions; reopen the archive and reproduce the same frame.

## Regression corpus and proposed sequence

The repository's existing tests primarily exercise transport/persistence and Fusion API doubles. Preserve those and add live Windows/Fusion fixtures covering the failures above. Use reduced synthetic hardware where third-party model redistribution is not authorized. Record Fusion/bridge versions, expected measurements, tolerances and known limitations.

Record this run's evidence accurately: native batch editing/export worked; 1,233 nominal native interference checks at 56 verified poses passed; the final archive reopened with four printed solids and 11 joints; all four parts generated slicer toolpaths. These results validate these workflows and this sampled geometry, not every API wrapper or physical manufacturing outcome. Several checks used custom scripts because existing helpers were insufficient.

Suggested sequence:
1. Reliability patch: root targeting, typed validation, document recovery, actionable diagnostics.
2. Verification/performance release: recompute policy, pose verification, geometry guards, surface and print audits, tolerance/path checks.
3. Authoring/release layer: constrained primitives, design-intent tags, synchronized BOM/manual/export and repeatable media capture.

References:
- https://github.com/mtorores-hash/ai-make-fusion-MCP/tree/workbench
- https://github.com/mtorores-hash/ai-make-fusion-MCP/blob/workbench/docs/test-summary.md
- https://github.com/mtorores-hash/ai-make-fusion-MCP/blob/workbench/docs/troubleshooting.md
- Local installed code: C:/AI-Make/fusion-prompt-mcp/FusionPromptBridge/advanced.py, model_tools.py and batch_runner.py
- BRANCA evidence: outputs/R56_Final/verification_summary.json, native_checks.json, archive_roundtrip.json, print_audit.json and shell_analysis_final.json