# Fusion Parametric Modeling Standard

A practical field guide for clean, parametric Autodesk Fusion models that stay editable over their lifecycle.

There is no official Autodesk “bible.” This document distills community R.U.L.E. #1 / #2, Autodesk’s sketching and parameter guidance, Jeff Strater’s reference-stability rules, and the Go Fusion Experts modeling checklist.

## Contents

1. [Purpose](#purpose)
2. [Structure — R.U.L.E. #1 and #2](#structure--rule-1-and-2)
3. [Sketches](#sketches)
4. [Reference stability](#reference-stability)
5. [Parameters](#parameters)
6. [Features and timeline](#features-and-timeline)
7. [Assemblies](#assemblies)
8. [Lifecycle tools](#lifecycle-tools)
9. [Naming conventions](#naming-conventions)
10. [What not to do](#what-not-to-do)
11. [Before-you-save checklist](#before-you-save-checklist)
12. [Sources](#sources)

## Purpose

A parametric Fusion model is a recipe, not a snapshot. The goal is a file that someone else — or you, six months later — can open, change a few named parameters, and get a predictable update without yellow or red timeline icons.

Encode design intent in:

- Component structure
- Fully constrained sketches
- Named user parameters and equations
- A short, named, late-filleted timeline
- Joints and external components instead of ad-hoc moves

## Structure — R.U.L.E. #1 and #2

### R.U.L.E. #1 — Component first

When in doubt, before doing anything: **create a component, name it, and activate it.**

Everything created while that component is active (sketches, bodies, construction geometry, joint origins) lives inside that component’s timeline.

Why it matters:

- The component can be saved or copied with full parametric history
- Joints, drawings, BOM, isolate, and selection sets all require components
- Activating a component filters the timeline to that part only
- Modeling bodies in the root and converting later is the most common way Fusion files become hard to edit

Valid exceptions:

- A top-level skeleton / layout sketch that drives several parts
- A T-Spline or concept body you later split
- A single-part file that will be inserted as an external component (XREF)

Convert bodies to components as soon as they exist. Do not model a pile of bodies in the root and convert at the end.

Assembly-scale version of the same idea:

1. Create empty components first
2. Activate one component
3. Finish that part
4. Activate the next component
5. Repeat

### R.U.L.E. #2 — Name your stuff

Rename components, bodies, sketches, construction planes, and key timeline features immediately. `Sketch15` and `Extrude32` are why people rebuild models from scratch.

## Sketches

Sketches are where models live or die.

### Must do

- Fully constrain every sketch. Black geometry only. Nothing should drag.
- Anchor the first sketch to the **origin**.
- Constraints first, dimensions second. Prefer perpendicular, equal, coincident, midpoint, and symmetry over extra dimensions.
- Keep sketches small: roughly 20 entities and 5–10 dimensions. Split complex profiles.
- Sketch on origin planes or construction planes derived from the origin. Sketch on a part face only when that parent/child relationship is intentional.
- Project sparingly. Do not project fillets, chamfers, patterned children, or loft edges.
- Do not put fillets or chamfers in sketches unless they are functionally required. Make them late 3D features.
- Pattern and mirror in 3D, not in the sketch.
- Before finishing a sketch, change a key dimension and confirm the behavior.

### Avoid

- Blue (under-constrained) geometry. Fusion can nudge it without opening the sketch.
- The Fix constraint as a substitute for real constraints. It makes later edits harder. Reserve it for splines or exploded text.
- Duplicated dimensions for the same length. Use Equal or reference one master dimension.
- Overloaded DXF / SVG imports. About 100 sketch entities is already large; 250+ is usually unworkable. Break them up.

## Reference stability

When a sketch or feature must reference existing geometry, use the most stable source available. Jeff Strater’s order, most stable first:

1. Origin work geometry — never fails
2. Work geometry based only on the origin
3. Other sketch geometry
4. Bodies
5. Faces
6. Edges
7. Vertices — most fragile

Yellow warnings are usually broken projections. Prefer origin and work planes over faces and edges that will change when fillets or sizes update.

Build **low and wide**: a top-level skeleton sketch that child sketches reference. Do not chain component-to-component projections.

Unstable references to avoid parenting new features to:

- Faces and edges of fillets or chamfers
- Children of a pattern or mirror (reference the seed)
- Edges or seams of non-analytic surfaces
- Fixed or grounded cross-component projections

## Parameters

Open **Modify → Change Parameters**, or press `S` and type `param`.

### Create a source of truth

- Create **user parameters** for anything that will change over the lifecycle: `wall`, `hole_dia`, `clearance`, `overall_width`, `ply_thk`.
- Do not leave driving sizes as anonymous model parameters (`d12`, `d47`).
- Use a consistent naming scheme. Add comments that explain intent and limits.
- Star driving parameters as Favorites.

### Encode relationships as expressions

Do not copy the same number into ten dimensions.

```
rib            = wall * 0.6
hole_offset    = overall_width / 2
bolt_circle    = housing_od - 20 mm
shelf_spacing  = cabinet_height / 4
```

### Parameter hygiene

- Do not mix hardcoded numbers and parameters for the same family of dimensions.
- Avoid circular references.
- Test extreme values early — after the first few features, not after feature 80.
- Review the parameter list periodically and delete unused entries.
- Multi-file projects: keep a **master parameter file** and **Derive** those parameters into working designs. Only put truly global values in the master. Favorite the derived parameters in each child file or you cannot type them.
- Product families / print variants: use **Configurations** and Configuration Rules instead of Save-As copies or piles of suppressed features.

## Features and timeline

The timeline is the recipe. Keep it short, named, and honest.

### Order of operations

1. Origin-based sketches and base solids
2. Major additive / subtractive features
3. Holes and functional cuts
4. Draft
5. Fillets and chamfers
6. Cosmetic features: decals, embossed text

### Must do

- Fix yellow and red timeline features immediately.
- Rename features you will ever edit again. Group related features.
- Prefer origin-based work geometry over parent/child links to faces.
- For symmetric parts, model half and Mirror the body.
- Pattern 3D features, not sketches.
- Create multiple features from one shared sketch when the relationships belong together.

### Do not take shortcuts

- Do not fill a hole to remove it. Delete the hole feature.
- Do not stack extrudes to lengthen a part. Edit the original dimension.
- Do not suppress a feature and model around it as a way to finish the design.
- Do not use Move Face as a substitute for editing the sketch.
- Do not leave unused or suppressed features past the end-of-component marker.

### Making a large change

1. Drag the End of Part marker to just after the feature you are editing
2. Change values in stages (1 → 3 → 6 → 10, not 1 → 10 in one jump)
3. Roll the marker forward
4. Repair each broken feature before continuing

## Assemblies

- Prefer **external components** for anything reused or released.
- Position with **Joints**, not Move / Align + Capture Position.
- Capture Position is computationally heavy and is not a good parametric relationship.
- Keep assemblies near the origin and aligned to it.
- Pin the first component with an in-place rigid joint. Fusion Ground is not the same as SolidWorks Ground.
- Nest subassemblies. Do not build one giant flat assembly.
- Put joint origins on stable geometry inside the component.
- Watch the blue dots on assembly contexts. They mean an in-context reference is stale.
- Reuse an assembly context when creating associative features, instead of spawning extra contexts.

## Lifecycle tools

| Need | Tool |
|---|---|
| Size or option family in one file | Configurations + Configuration Rules |
| Shared numbers across many files | Master parameter file + Derive |
| Meaningful checkpoints | Create Version with a written description |
| Daily progress notes | Save descriptions, not extra versions |
| Imported or history-less geometry | Find Features, then Capture Design History |
| Newer path for history-less geometry | AutoTimeline (recovery tool, not an authoring substitute) |
| Reuse without breaking the source | External component, or Derive objects from the top-level component |

Create a named version before changing driving parameters, before a design review, and before a manufacturing release.

## Naming conventions

| Object | Pattern | Example |
|---|---|---|
| Component | noun; underscores if needed | `housing`, `lid`, `toolhead_left` |
| Body | same as component if 1:1, else role | `housing_body`, `rib_inner` |
| Sketch | `sk_` + role | `sk_profile`, `sk_holes`, `sk_layout` |
| Construction | `pl_`, `ax_`, `pt_` + role | `pl_midplane`, `ax_hinge` |
| Feature | verb + what it does | `ext_housing`, `cut_pocket`, `fillet_edges`, `pat_m4` |
| User parameter | snake_case, units implied | `wall`, `hole_dia`, `clearance`, `overall_w` |
| Configuration | readable variant name | `M4_2mm`, `M5_3mm`, `left_hand` |

Keep parameter names short enough to type, unique enough to autocomplete. Comments on parameters should say what should change and what should not.

## What not to do

1. Model bodies in the root, then convert to components
2. Leave sketches under-constrained (blue)
3. Sketch on faces and project fillet / pattern / loft edges
4. Repeat magic numbers instead of named parameters
5. Put fillets, chamfers, holes, and cosmetics early in the tree
6. Fill a hole instead of deleting the hole feature
7. Stack extrudes to lengthen a part instead of editing the dimension
8. Use Move Face or Direct Edit on a native parametric part you still need to iterate
9. Use Capture Position as a substitute for joints
10. Leave yellow or red timeline items
11. Use the Fix constraint as a substitute for real constraints
12. Never test a parameter change until the model is “done”

## Before-you-save checklist

- [ ] Active work is inside the correct named component
- [ ] New sketches, bodies, planes, and key features are named
- [ ] Sketches are fully constrained and anchored
- [ ] Driving sizes are user parameters or expressions, not raw repeats
- [ ] No new projections from fillets, pattern instances, or changing faces
- [ ] Timeline has no yellow or red features
- [ ] Fillets / chamfers / draft are still late, or there is a reason they are not
- [ ] Joints used instead of Capture Position
- [ ] A key parameter was changed and the model updated as intended
- [ ] Version comment describes the intent of this save

## Sources

- [Fusion Modeling Best Practices](https://gofusionexperts.com/2023/08/27/fusion-modeling-beat-practices/)
- [Sketching and Parametric Basics (Autodesk, May 2026)](https://www.autodesk.com/products/fusion-360/blog/sketching-basics-in-autodesk-fusion/)
- [Mastering Fusion Parameters (Autodesk)](https://www.autodesk.com/products/fusion-360/blog/mastering-fusion-parameters-a-guide-for-simplified-design-control/)
- [Parameters in Fusion (help)](https://help.autodesk.com/view/fusion360/ENU/?guid=SLD-MODIFY-PARAMETERS)
- [Configurations overview (help)](https://help.autodesk.com/view/fusion360/ENU/?guid=CFG-OVERVIEW)
- [R.U.L.E. #1 and #2 (TrippyLighting, Autodesk forums)](https://forums.autodesk.com/t5/fusion-design-validate-document/fusion-r-u-l-e-1-and-2/td-p/6581749)
- [Ace Makerspace — parametric design practices](https://www.acemakerspace.org/best-practices-for-parametric-design-in-fusion-360/)
- Product Design Online — Rule #1 / bodies vs components and Learn Fusion in 30 Days
- Autodesk University — Phil Eichmiller, Large Design Management in Fusion 360
- [Best practices for robust parametric designs (Jeff Strater)](https://forums.autodesk.com/t5/fusion-design-validate-document/best-practices-for-robust-parametric-designs/td-p/9112280)
