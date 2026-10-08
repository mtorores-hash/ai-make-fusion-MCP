# Fusion modeling rules — AI Make

Rules version: 1.0.5. Supplied by Mauricio; applied to native parametric authoring.
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

## Connection selection and fastener review

Choose the physical connection before modeling hardware. Prefer the simplest connection that
satisfies loads, motion, assembly, manufacturing and service needs. Do not add screws or nuts
without identifying their purpose. A Fusion kinematic joint alone does not define a physical
attachment.

1. Consider one-piece construction when material, manufacturing/print orientation and service
   access permit. Do not merge parts that need motion, replacement or separate manufacture.
2. Define required motion and load path. Distinguish permanent assembly, occasional servicing
   and frequent access; account for vibration, wear, creep and material limitations where relevant.
3. Separate locating, load-bearing, retention and clamping functions. Consider shoulders,
   locating pins, tongues/grooves and interlocking geometry; do not assume screws must do every job.
4. Compare feasible options using hardware count/types, assembly steps, tool access, print
   difficulty and failure modes. Reuse suitable standard hardware; avoid arbitrary fastener-count
   limits or elaborate printed mechanisms that are worse than a simple screwed connection.
5. Record unknown loads/service needs as assumptions; ask when they materially change selection.
   Do not present an unverified choice as an ideal or validated joint.

Candidate guide (evaluate suitability, not automatic prescriptions):
- Permanent same-material structure: one-piece construction.
- Removable alignment: locating features plus minimal retention.
- Frequent-access cover: captive screws, latch or suitable snap-fit.
- Occasionally serviced printed assembly: screws with suitable inserts or captive nuts.
- Sliding/interchangeable module: guide or dovetail with a stop/lock.
- Rotation: axle/pivot, appropriate bearing surfaces and axial retention.
- Permanent dissimilar materials: suitable adhesive or mechanical retention.

For each distinct connection, keep a short project record:
purpose → loads/motion → service frequency → selected connection → reason a simpler alternative
was rejected (or why none is needed) → assembly/access check. Repeated identical connections may
share one rationale.

Before completion, review redundant screws, inaccessible nuts, unnecessary hardware sizes,
assembly order and opportunities to consolidate parts. Retain necessary clamp/load capacity
and inspect insertion, tightening and removal access. Do not substitute snap-fits, adhesives
or press fits without checking their material, tolerance and service requirements.
This is design guidance plus manual review, not an automatic joint optimizer or strength proof.

## Junction completeness

A successful join, healthy feature or single solid body does not prove that a junction is
complete, sufficiently thick or smoothly transitioned. Verify the intended local geometry.

- Classify each critical junction as continuous material, an intentional seam or a moving
  interface. Preserve designed gaps, reliefs and sharp functional edges.
- For continuous parts, connect ribs, bosses and walls across the intended attachment area.
  Reject accidental gaps, point/edge-only contact, thin slivers and unintended partial-width
  attachments. Define minimum attachment width/thickness from design and manufacturing needs;
  do not invent one universal threshold or treat body count as proof of adequate connection.
- Prefer shared profiles, correctly terminated ribs and controlled lofts/transitions. Correct
  the source geometry rather than accumulating patch features or hiding defects with fillets.
- After relevant edits and regeneration, inspect sections through AND beside each critical
  junction. Measure the attachment width and local thickness against the stated requirements.
- Where a smooth blend is intended, require tangent continuity and inspect the transition;
  use zebra/surface analysis where available. Deliberate sharp boundaries need no forced blend.
  Surface smoothness alone does not establish solid connectivity or structural adequacy.
- Before completion, retain a close-up, section evidence and measured values for each critical
  junction in the design project. Identify the junction and model revision; refresh evidence
  after edits affecting it. Resolve unintended discontinuities before declaring completion;
  report unresolved findings and keep any interim export clearly marked as work in progress.

These are authoring and manual-review requirements. The current hygiene audit does not
automatically measure junction thickness, prove attachment completeness or verify tangency.
Its passing result cannot substitute for this evidence.

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
restored timeline, commercial-hardware sourcing/fidelity, junction evidence, connection selection/fastener review and save description. Automatic checks cannot infer all of these.

## Fusion cloud files and shared human/AI editing

Use Fusion cloud storage as the editable CAD source of truth. Select the intended hub and
create/reuse a named project with `Assembly`, `Parts`, and `Purchased Components` folders.
Save independently editable custom parts as descriptively named native Fusion documents;
assemble them with external references where useful. Use stable cloud file IDs and versions
for identity, not filenames or transient entity tokens. Record the project, folder, part IDs,
assembly links and current versions in the design project's handoff. Keep supplier originals.

Before resuming, inspect the open document, unsaved changes, cloud versions, components,
parameters and reference health. Call `inspect_document_state` before each mutation and pass
its single-use `edit_token`. If anything changes, reinspect and adapt to the user's work.
Do not replace manually designed geometry, discard unsaved edits, break links or rebuild a part
from an old script. Opening a cloud file must preserve other open documents. Update selected
references deliberately, then check joints, geometry and interference before saving the assembly.

Save new versions of the same file; do not proliferate renamed duplicates. Confirm cloud
processing is complete before handing work back. Leave a short handoff naming the project,
assembly, parts changed, versions and remaining checks. The user should be able to open a part,
edit it normally in Fusion and save; subsequent AI work continues from that saved design.

Cloud copies of existing internal components do not automatically become linked replacements.
Preserve the original assembly and joints; migrate deliberately after inspection. For linked
assemblies, checkpoint a clean completed cloud version plus its reference-version manifest.
Do not call a cloud manifest a self-contained F3D archive. Split long changes into save/inspect/
checkpoint stages when needed. Optimistic guards do not provide distributed locking or sandbox
trusted Python. Never replay an interrupted/uncertain cloud mutation under a fresh operation ID.
