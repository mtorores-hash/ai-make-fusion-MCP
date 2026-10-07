# Fusion modeling rules — AI Make

Rules version: 1.0.2. Supplied by Mauricio; applied to native parametric authoring.
Read these rules before modeling. Project-specific instructions and explicit user decisions
control dimensions, materials, fits and documented exceptions. Report a conflict rather
than quietly dropping a rule. Preserve existing models and imported hardware.

## Required authoring behavior

1. **Component first.** Create, name and activate the intended component before interactive
   authoring. With the API, create geometry through that component's collections and verify
   ownership; selecting `ctx.target` does not activate it or redirect arbitrary `adsk` calls.
   Root skeleton/layout sketches, temporary concept/T-Spline work and a single-part external
   source file are valid exceptions. Do not accumulate unrelated root bodies and convert at the end.
2. **Name immediately.** Name components, bodies, sketches, construction geometry and editable
   features by purpose. Use `sk_`, `pl_`, `ax_`, `pt_`; features such as `ext_housing`,
   `cut_pocket`, `fillet_edges`, `pat_m4`; user parameters in snake_case. Do not rename purchased
   hardware, overwrite supplier identifiers or bulk-rename existing designs without task scope.
3. **Constrain sketches.** Native authored sketches must be fully constrained, with an intentional
   origin/reference anchor. Apply geometric constraints first, then driving dimensions.
   Fix is not a substitute for design intent; spline/exploded-text uses need an explicit reason.
   API `isFullyConstrained` is a useful test, not proof of proper anchoring or useful constraints.
4. **Drive real geometry.** Create named user parameters for lifecycle-driving dimensions and
   use them in sketch/feature expressions. Reuse master dimensions and relationships, not copied
   literals. Add intent/limit comments and Favorite driving parameters. Anonymous `d12` parameters
   may legitimately remain internal; do not rename every generated model parameter. Test meaningful
   parameter changes and extremes early, on a checkpointed copy, and record expected versus observed
   effects. Unused labels are not parametric design.
5. **Healthy timeline.** Resolve yellow/red sketch/feature/joint warnings and errors before declaring
   work complete. Edit the source dimension/feature instead of stacking repair extrudes, filling holes,
   or using Move Face to disguise an editable design change. Group related timeline work.
6. **Preserve interfaces.** Keep functional bores, datums, shoulders and washer seats protected.
   Do not indiscriminately round edges or delete apparently unused/suppressed items without review.
7. **Evidence before release.** Synchronize after geometry edits; run `audit_modeling_hygiene` or
   `ctx.audit_hygiene()`, resolve violations, and explicitly review the items automation cannot prove.
   Exercise a driving parameter, restore it, verify health and dimensions, and record the evidence.
   Save/version descriptions should explain intent. Local F3D checkpoints are not cloud versions.

## Commercial hardware models

For every purchased component, use an accurate CAD model when available. Follow this order:

1. **Search online first.** Identify the manufacturer, exact part number and variant. Prefer
   manufacturer/supplier CAD, then reputable CAD libraries. Prefer usable native/STEP solids;
   visual detail alone is not quality. Check units, envelope, mounting pattern and critical
   interfaces against the product drawing. Do not substitute a similar-looking variant.
2. **Ask the user.** If no suitable model is found or accessible, summarize the search and
   ask whether the user has the CAD file. Allow their answer before proceeding for that
   component; continue independent design work while waiting.
3. **Reconstruct from specifications.** If the user has no model, find manufacturer drawings
   or spec sheets online and model the documented geometry. Preserve critical interfaces;
   identify missing dimensions and assumptions. Label it as reconstructed, not supplier CAD.
4. **Placeholder last.** Only after those routes are exhausted, use a clearly named
   placeholder for layout, state its assumptions and limits, and flag it for replacement.
   Do not claim verified fit, clearance or motion from guessed geometry.

Record source URL/file, part/variant, model status (supplier, third-party, reconstructed or
placeholder), and checked dimensions in the project record. Keep source identifiers intact.
Use the model's applicable sharing terms; obtaining CAD does not imply redistribution rights.
Search, sourcing quality and dimensional fidelity require AI/user review; the hygiene audit
does not automatically verify them.

## PCB connectors, pins and cables

Unless the user explicitly requests detailed connector or pin geometry, model PCB connectors
and pin groups as simple clearance volumes. Preserve their location, board side, orientation,
outer envelope and protrusion; include mating-plug/insertion space where relevant. Omit
individual contacts, pin-by-pin geometry and cosmetic connector detail.

Route cables as simple paths or swept envelopes toward the appropriate connection area on the
board, with the correct mating direction and cable exit orientation. Do not route to individual
pins or imply pin-level electrical connectivity. Account for cable thickness and required bend/
access space; label unknown dimensions or routing assumptions.

This is an intentional detail-level exception to the commercial-hardware CAD rule: use sourced
CAD or drawings to establish accurate envelopes, but do not rebuild detailed connectors or pins.
Preserve original supplier models; use simplified representations for layout/clearance work.
A source-backed envelope is a simplification, not a guessed placeholder. Apply the sourcing
fallback order when dimensions are unavailable. Review clearances and routing manually;
the hygiene audit cannot automatically verify envelope fidelity or cable orientation.

## Preferred modeling strategy — review, not universal numeric gates

- Keep sketches small: roughly 20 curves and 5–10 dimensions. At 100 curves review splitting;
  at 250 or more review performance carefully. These are heuristics, not kernel limits. Count
  curves and dimensions separately; a fully constrained large sketch is not automatically invalid.
- Prefer origin geometry, then origin-derived work geometry, sketches, bodies, faces, edges, vertices.
  This is a reference-stability preference, not a guarantee that any reference can never fail.
- Use a low, wide skeleton hierarchy. Avoid chained cross-component projections and references to
  fillet/chamfer edges, patterned children or non-analytic seams. Face-based sketches are allowed
  when their parent/child relationship is intentional and documented. Prefer pattern seeds.
- Model base solids, major additions/removals, functional holes/cuts, draft, then cosmetic fillets/
  chamfers and appearance details. Functionally necessary early rounds are documented exceptions.
  Do not move functional holes to the end merely because a summary says “holes late.”
- Prefer 3D feature/body patterns and mirrors. Choose a shared sketch when it expresses common
  relationships; split it when it becomes overloaded. Half-model/body-mirror is appropriate for
  truly symmetric parts, not an unconditional instruction to rebuild imported/asymmetric geometry.
- For large edits, roll the timeline to the relevant stage, change in sensible increments and repair
  downstream failures as it advances. Restore the intended end position; do not leave features hidden
  beyond the marker. Do not force history conversion or delete original imported geometry automatically.
- Use joints and stable joint origins for mechanism relationships. Avoid Move/Align/Capture Position
  as a substitute for joints. Review the intended fixed reference and available grounding/rigid-joint
  behavior for this design; do not automatically add an in-place rigid joint to every first component.
- Prefer reusable external components and nested subassemblies where appropriate. External links can
  prevent this bridge's local F3D checkpoint workflow: resolve that conflict explicitly, preserve source
  links, and never silently skip backup or break links.
- Review stale assembly contexts. Reuse suitable contexts. Keep origins/axes intentional.
- Use Configurations for product families and master/derived parameters for truly shared values when
  supported by the installed Fusion version and license. Do not assume UI/version-specific tools
  such as history recovery are present or run them automatically.

## Exceptions and checks

The audit distinguishes deterministic violations, advisory reviews, unavailable inspection and
manual review. It never edits geometry, fixes sketches, deletes parameters or moves timeline items.
A zero-violation result covers the automated subset only; it is not full design approval.

`ctx.export_checked(...)` enforces the automated subset before exporting and requires a written
manual-review note. Unavailable required inspection fails closed. It can optionally block advisories.
Plain `ctx.export`, native `adsk` exports and recovery checkpoints remain available: unrestricted
Python is not a global save interceptor. Do not use those paths to claim a failed audit passed.
If a legitimate imported/concept exception is flagged, record it and use a clearly identified working
export pending review; there is no invisible auto-waiver. This first auditor covers the whole design,
including native definitions of linked components; report source ownership before suggesting repairs.

Before calling the model finished, confirm component ownership/names, constraints and anchoring,
parameter usage and perturbation, reference stability, feature ordering/health, joint intent,
restored timeline, commercial-hardware sourcing/fidelity and save description. Automatic checks cannot infer all of these.
