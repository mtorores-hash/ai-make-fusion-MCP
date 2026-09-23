# Fusion modeling rules — AI Make

Rules version: 1.0.0. Supplied by Mauricio; applied to native parametric authoring.
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
restored timeline and save description. Automatic checks cannot infer all of these.
