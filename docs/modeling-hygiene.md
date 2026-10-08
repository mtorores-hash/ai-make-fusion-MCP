# Modeling hygiene — v0.4.1

Mauricio supplied [Fusion-Parametric-Modeling-Best-Practices.md](Fusion-Parametric-Modeling-Best-Practices.md)
as the authoring standard. That file is preserved verbatim. [modeling-rules.md](modeling-rules.md)
is the operational interpretation, also shipped byte-for-byte with the installable software.
No geometry was modified while introducing these rules.

## How connected AI clients receive the rules

- MCP initialization instructions tell the client to call `get_modeling_rules` before modeling.
- `get_modeling_rules()` returns the full installed rules text, version `1.0.3`, and SHA-256.
  It works without opening Fusion.
- Resource `fusion://modeling-rules` exposes the same text for clients that use MCP resources.
- Repository `AGENTS.md` references the same rules for coding/modeling work.
- The AI should inspect the model, apply the project brief, model within named component
  collections, and run the hygiene audit before declaring completion.

The server cannot force every AI client to follow guidance, or intercept arbitrary `adsk` saves.
Audit results expose what was actually checked. The installed rules file must be copied along
with the Python modules; this is not a remote policy that silently changes an old installation.

## Automated audit

Call `audit_modeling_hygiene(design_id)` or `ctx.audit_hygiene()` in a batch. Both inspect
component definitions throughout the design, including linked/imported definitions, and return
one JSON report. Neither regenerates or edits the model. Synchronize geometry edits before auditing.
Read-only batches may call `ctx.audit_hygiene()` with literal arguments under the existing restricted grammar.

| Rule | Automated outcome | Limits |
| --- | --- | --- |
| Parametric design history | Error for non-parametric design | No automatic conversion of imported/history-less models |
| Purposeful object names | Error for blank or recognizable English default names (`Sketch15`, `Extrude32`, etc.) | Semantic meaning/localized defaults cannot be proven; imported identifiers preserved |
| Naming prefixes | Review for sketch/construction prefix deviations | Component/feature intent still reviewed manually |
| Sketch fully constrained | Error when Fusion returns false | Does not prove origin anchoring, absence of redundant constraints or editability |
| Yellow/red sketch/feature/joint health | Error | Other nonhealthy states require review; fixes are never automatic |
| Root bodies | Review | Single-part external sources and concept-body exceptions remain valid |
| Sketch complexity | Review above 20 curves or 10 dimensions; larger review bands at 100/250 curves | Heuristics, not Fusion limits; points/text are not included in curve count |
| Fixed sketch entities | Review fixed curves/non-origin points | Legitimate spline/text uses are not automatically condemned |
| User-parameter naming, comments, Favorites | Review | Not every user parameter is a driving input |
| No dependent parameter equations | Review | Does not establish non-use by every Fusion feature; no auto-delete |
| API property/collection unavailable | Explicit unknown; audit incomplete | Missing data cannot become an automated pass |

Every finding includes rule ID, severity, entity information and explanation. Parameters may have
no entity token; no synthetic token is invented. The whole-design scope can report legacy/imported
issues outside a current part's task. Inspect ownership before proposing a repair.

Reports distinguish `automated_checks_passed`, `inspection_complete`, `error_count`, `review_count`,
`unavailable_checks` and `manual_review_required`. **`full_standard_verified` remains false**:
the automated subset cannot prove reference stability, parameter perturbation, design intent,
feature order, proper joint strategy or save descriptions.

## Explicit checked-export gate

```python
def run(ctx):
    # Build using the retrieved rules, then perform and record the manual checks.
    return ctx.export_checked(
        'housing.f3d',
        manual_review_note='References reviewed; wall parameter varied/restored and dimensions checked. See project check record.'
    )
```

The helper synchronizes, audits, records the report, and exports only when automated checks pass.
It requires a nonempty manual-review note; that note is caller-reported evidence, not an automatic
proof. `strict_reviews=True` also blocks advisory findings. Defaults allow advisory reviews with
an explicit note. Include the actual project review evidence rather than copying an example claim.

`ctx.require_hygiene(strict_reviews=False)` records the report and raises on violations or
incomplete inspection without exporting. `ctx.export_checked` returns the exported artifact/hash,
full audit and manual note. Checkpoints, plain `ctx.export`, native exports and ordinary save remain
available for recovery and work in progress. They do not imply hygiene compliance. No audit gate
is inserted into recovery checkpoints or every modeling batch, so an incomplete sketch can still
be saved for further work. There are no silent auto-waivers for known failures.

## Interpretation decisions

- Curve/dimension counts are approximate design heuristics, not hard blockers.
- Origin geometry is preferred; “never fails” is not a universal guarantee.
- Functional holes belong with functional cuts. The source's short “holes late” summary does not
  override its detailed feature-order section.
- Native API geometry ownership comes from the component collections used, not merely the active
  UI component or the value of `ctx.target`.
- “Fully constrained” alone is not proof of anchoring or useful constraint design.
- An anonymous internal model parameter is not inherently wrong; lifecycle-driving values should
  reference named user parameters. Do not rename all internal `dN` values automatically.
- Ground/rigid-joint strategy, history recovery, Configurations/Derive and Favorites behavior depend
  on context and installed support. They are guidance for review, not guessed automated operations.
- External-component reuse can conflict with local F3D checkpoints. Preserve source links and resolve
  the backup workflow explicitly rather than breaking links or suppressing a checkpoint failure.

## Installation and live acceptance

Update the complete `software/fusion-prompt-mcp` folder, including `modeling-rules.md` and the
new `FusionPromptBridge/modeling_rules.py` and `hygiene.py`. Restart Fusion and the MCP process.
`fusion_capabilities` should report `0.4.1`, `modeling_hygiene_audit: true` and
`modeling_rules_version: '1.0.3'`. The MCP exposes 25 tools. See [installation](installation.md).

On a COPY of a local design:

1. Retrieve rules and verify the tool/resource text agrees.
2. Run the audit without mutations. Inspect names, under-constrained sketches and unknown API data.
3. In a disposable fixture, leave a sketch under-constrained and confirm checked export creates no file.
4. Constrain/name it properly and rerun. Confirm the fixed origin is not reported as misuse of Fix.
5. Confirm a valid root-body exception or intentionally large sketch is a review item, not an automatic repair.
6. Confirm recovery checkpoints still work when the hygiene audit fails.

Automated numerical/API-double and protocol tests are recorded in [test summary](test-summary.md).
No new live Fusion/kernel validation is claimed. Mauricio reported v0.4 running; that report does
not validate v0.4.1 inspection or export paths.

## Primary API contracts checked

- [Sketch.isFullyConstrained](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Sketch_isFullyConstrained.htm)
- [Sketch.healthState](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Sketch_healthState.htm)
- [SketchCurves.count](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SketchCurves_count.htm)
- [SketchCurve.isFixed](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SketchCurve_isFixed.htm)
- [Sketch.originPoint](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Sketch_originPoint.htm)
- [UserParameter.comment](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_UserParameter_comment.htm)
- [UserParameter.isFavorite](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_UserParameter_isFavorite.htm)
- [Parameter.dependentParameters](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Parameter_dependentParameters.htm)

## Commercial hardware sourcing (rules 1.0.1)

The served rules require online CAD search, then asking the user, then reconstruction from
published specifications before using a labeled placeholder. Verify part/variant and critical
dimensions; record source and model status. The audit includes this in manual_review_required;
no automatic web search or supplier-model fidelity check is implemented. A checked export's
manual review must address this requirement when purchased components are present.

## PCB representation (rules 1.0.2)

Use simplified connector/pin clearance volumes and cable paths to the correct board region
and orientation unless detail is explicitly requested. Source-backed simplification is an
exception to detailed commercial-hardware representation; preserve original supplier CAD.
The audit lists envelope accuracy and cable routing/orientation for manual review, not as
an automatically verified geometry check. See modeling-rules.md for the full requirement.

## Junction completeness (rules 1.0.3)

The served rules require classifying connection intent, complete intended attachment, measured
local width/thickness and surface continuity where intended. Retain current close-up and section
evidence in the design project; repair source geometry and resolve unintended discontinuities
before completion. Preserve intentional gaps, moving interfaces and functional sharp edges.
The manual_review_required checklist includes this requirement. The audit does not automatically
validate attachment area, local thickness, tangency or evidence files; checked-export notes must
reference that review for critical junctions. A healthy feature or one solid is insufficient.
