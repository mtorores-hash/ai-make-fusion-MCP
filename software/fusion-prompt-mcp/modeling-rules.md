# Fusion modeling rules — AI Make

Rules version: 1.3.0. Caller contract: 2.0. Runtime: 0.8.0 development.

These are operational CAD rules. The caller's approved task supplies intended use, dimensions,
manufacturing context, phase/milestone, active configuration and permitted changes. The MCP
performs CAD work and reports evidence; it does not set the PDS, approve designs, reopen frozen
parts, choose agents/models, allocate credits or synchronize GitHub. Approval references are
caller assertions, not independently authenticated permissions. The supplied best-practices
compilation remains reference material; this file is the single active installed standard.

## Before work

Observe the actual document and inspect the assigned part and relevant interfaces. Preserve
existing native work and manual edits. Use stable cloud file IDs/versions for saved identity;
resolve transient entity tokens before acting. Never use visibility or a name to infer retirement.

Get these rules once, retaining their version and SHA-256. Subsequent callers may send the known
hash; unchanged rules omit the text. Changed hashes return the current full rules.

For bounded work supply contract 1.0 `scope` and `task`. Separate current `membership` (active,
retired, archived) from `maturity` (working, frozen). A frozen part can be active and necessary
for integrated checks. Declare selected targets, directly relevant dependencies, required checks,
parameter names, representation roles and baseline revisions. Missing required evidence remains
unproven. Routine checks do not assign repair of unrelated old findings to the current task.

Acquire a writer token with the designated writer ID; ordinary state observation is read-only.
Use the token once with the exact accepted reference pins. A target and token alone do not impose
an edit allowlist. Narrow supported tools prevent known out-of-scope changes; unrestricted Python
is trusted, with observed postconditions only. Do not interactively edit during a batch.

## Native authoring

- **Component first.** Author through the intended native component's collections. A single-part
  external source file, intentional root layout/skeleton or concept study is a valid declared use.
  Selecting `ctx.target` neither redirects raw API calls nor creates a sandbox.
- Name newly authored components, bodies, sketches, construction geometry and features by purpose.
  Prefer `sk_`, `pl_`, `ax_`, `pt_`; readable feature names and snake_case driving parameters.
  Preserve supplier identifiers and valid existing geometry; do not rename everything for an audit.
- Constrain native build-functional sketches deliberately: anchor/reference intent, geometric
  constraints, then driving dimensions tied to named parameters. Do not use Fix as a blanket repair.
  Necessary spline/text exceptions and intentional constants require a scoped explanation.
- Keep sketches and features understandable; split unrelated functions. Complexity counts are
  review heuristics, not permission for unsolicited refactoring or arbitrary validity limits.
- Use meaningful units, parameter comments and intentional dependencies. Inspect intended edits,
  recompute, and preserve the original parameter expression when exercising a parameter.
- Check critical parameter behavior and design extremes at the relevant milestone. Reuse unchanged
  evidence with complete dependency records; do not perturb every parameter after every edit.
- Keep feature history healthy where relevant. Repair the source of a real defect rather than
  layering cosmetic patches. Preserve legitimate source history and imported/linked ownership.
- Root-only rectangle/circle/extrude tools are **concept primitives**; they do not promise fully
  constrained component-owned parametric authoring. Reuse `ctx.parametric_circle` with an existing
  named length parameter for an anchored, diameter-driven native profile. It checks the solver's
  constrained flag; native behavior still requires approved disposable Fusion acceptance.

## External hardware, electronics and wiring

During Detail Design use the minimum functional geometry needed for envelope, mounting, movement,
mating, access and clearance decisions. Separate provenance from detail. An exact supplier model
and a drawing-derived, source-grounded envelope are both valid. A sufficient drawing/envelope
need not wait for richer supplier CAD. Verify the exact variant and critical interfaces; retain
sources, revisions and unknowns. Keep original supplier assets separate from simplified working
geometry. A guessed placeholder remains labeled and cannot substantiate verified fit.

When essential interface data is missing, look for useful supplier CAD/drawings, ask the user for
available models or measurements, then reconstruct what is supported. Stop or carry a documented
assumption according to the approved task; do not silently invent dimensions or claim missing proof.
Defer aesthetic supplier detail until the approved design stage unless its functional value is clear.

For PCBs/electronics use board and connector envelopes, mating/exit orientations and general cable
routes to the correct board area. No default pin-by-pin, detailed connector or cable construction.
Higher fidelity follows the caller's approval rule: flag the specific mechanical risk and expected
value, and obtain the required approval before increasing detail. Preserve the simplified model's
limits; a routing envelope is not detailed cable-clearance proof.

## Connections and junctions

Choose how parts locate, transmit load, retain and move early. Consider consolidation, service,
manufacturing and tool/assembly access before adding hardware. Record a short rationale for each
distinct connection. Finalize exact fastener specifications, lengths, quantities and engagement
once interfaces stabilize. Full screws, threads, pins, inserts and service features are not compulsory
outside the approved use case. Avoid redundant or inaccessible fasteners without inventing elaborate
printed connections to minimize hardware count.

Declare junction intent. For intended material continuity, verify complete local attachment and
necessary width/thickness; a Join operation or single body does not prove a sound junction. Use
close-ups, sections and dimensions where the interface warrants them. Keep intentional sharp edges,
clearances, separable contacts and motion gaps. Blend only where function/intended transition calls
for it. Reuse current evidence until its relevant geometry changes; scope reviews to the milestone.

## Inspection, validation and export

Use selected-part/subsystem checks by default for task work. Explicit full-design checks remain
available for integrated release or diagnosis. Omitted scope on legacy audit/validation tools retains
the old whole-design path; new callers should pass the selected contract. Unrelated supplier naming
is not an authored-part requirement. Untouched references get relevant health and source-grounded
interface evidence checks, not mandatory sketch reconstruction. Modified external geometry is
subject to authoring checks as applicable, without destroying the preserved source.

Keep execution, feature integrity, functional evidence, readiness and human approval distinct.
Report new damage anywhere, relevant old failures and unrelated old findings separately. New damage
outside the permitted edit set fails the operation. Required unknown data is not green. Explicit
non-applicability carries a reason and is neither a pass nor an override of a required applicable check.

Checked export must match a nonempty, live, revision-current target scope. A parent export must not
silently include unselected descendants. Validate the exported part and relevant dependencies;
return applicable checks, exclusions, evidence gaps and revisions. Never label a selected pass as a
whole-assembly pass. Working/recovery exports remain available and must not be represented as checked
manufacturing approval. Do not globally disable validation to escape a failure.

Use geometry-based selection and verify ambiguity after edits. World-space checks require occurrence
context. Interference and clearance checks apply only to the selected geometry and stated pose/path.
Sampled motion is discrete evidence, not continuous proof; use the approved acceptance method and
state its limits without adding an unrequested continuous-proof requirement. CAD and API doubles
never establish physical execution, material strength, installed Fusion correctness or human approval.

Evidence reuse uses exact declared dependency revisions, or the bounded BRep/placement/declared-
parameter fingerprint. Component-name changes do not enter the latter. Body revisions, interface
geometry and placements do; incomplete mesh/sketch-only records remain unproven. The caller owns
completeness of functional dependencies. Do not pretend a cached measurement covers an omitted input.

## Cloud saving, recovery and retirement

Use named native Fusion part documents in an explicit project, with Assembly, Parts and Purchased
Components folders where appropriate. Save versions of the same file, not renamed duplicates. Keep
cloud IDs/versions and a short part/assembly handoff so the user can edit a part normally and the AI
continues from that design. Cloud saves are independent of GitHub synchronization.

Intentional reference pins may remain older than available versions. Supply the accepted exact
reference set; report updates without forcing them. A stale editing target remains blocked even when
historical inspection is allowed. Never discard dirty user work, silently reload, break links or
replace manually designed geometry to get past a guard.

For dirty assemblies with stale dependencies: observe, accept the current exact pins, acquire a token,
save and poll completion, then deliberately update the selected reference. Save with the remaining
pins before the next update. Saving preserves work; it does not approve the design.

Local unlinked checkpoints are self-contained F3D archives where Fusion supports export. Linked
checkpoints are clean completed cloud-version/reference manifests, not standalone archives. Split
linked work into sensible edit/save/checkpoint stages. Disposable F3D experiments reject linked
assembly targets before regeneration; use a separately saved unlinked part when appropriate.
No automatic link migration, joint transfer, rollback or competing assembly rebuild is authorized.

Reuse the identical operation ID/request after connection loss. Cancelled monitoring does not stop
an upload. Uncertain saves block later mutations until the original job and observed cloud version
are reconciled. Caller confirmation is recorded as such, not authenticated proof of execution.
Never retry an uncertain operation under a fresh ID.

Retire caller-identified occurrences using the dedicated supported Remove-feature path, not hiding,
suppressing or parking them. Preserve source files, shared active definitions and harmless history.
The current narrow tool supports top-level leaf occurrences only, rejects live joint/rigid-group or
subtree dependencies and reports its dependency-review limits. Stop on blockers or partial changes.
Return lifecycle facts for the caller to reconcile; the MCP does not update external BOM/graph/site
records or authorize a frozen part's reopening. Archived definitions without live occurrences stay
outside current scoped QA and manufacturing selection.

## Declared interfaces and physical assembly evidence

Before detail work, declare mounting datums, protected mating surfaces, critical dimensions, source/uncertainty and body revision. Specify joining intent and insertion direction before choosing hardware. Reserve connected connector/wire-bend volumes, driver and fastener paths, heatset installation space and service removal paths. Conservative sourced envelopes are sufficient; default to no detailed PCB pins or irrelevant threads/cosmetics.

Build one coherent controlling profile for a continuous wall. Declare where seams, ribs, chamfers, press interference and functional stops are intentional. Use the existing surface audit plus the bounded engineering plan where applicable. A short edge is a review candidate, not automatically a defect. Review critical junctions locally with measured points/sections. Native health, geometric quality, assembly feasibility and manufacturing readiness are separate conclusions; none proves acceptable appearance.

Use one scoped verification batch for the affected interface dependency closure. Reuse evidence only when requirements, resolved geometry, body revisions, placements, datums and declared parameters still match. Undeclared dependencies, failed evaluators and gaps remain unproven. Do not increase sample counts or repeat broad audits without a concrete unresolved risk. Finite clear poses never prove continuous collision freedom.

Checkpoint major edits using named stages and actual postconditions. After failure report observed change or unknown; reconcile the original job, preserve completed stages and verify protected metrics. Never retry the same failed hypothesis with a fresh operation ID. Ask for the specific missing datum/reference/intent when it cannot be determined.

Handoff exports with generation-time geometry identity, declared print orientation/bed face, protected mates, allowed support regions/exceptions and overhang/bridge/access review. Verify source revisions and hashes. Actual bed contact, supports, printer profile, plate placement and per-object settings require slicer inspection. Geometry signatures are bounded guards, not full shape equivalence or manufacturing certification. See engineering-contract.md.

## Bounded authoring and outcome discipline (1.3)

Before a small edit, name the controlling source features, affected scope, protected members,
planned operations and justified feature/sketch additions. Adopt explicit per-change and
cumulative issue budgets through `task.authoring`; never invent universal thresholds.
Keep the same project-qualified issue ID across agent/job changes. Prefer correcting source
profiles and using patterns to chains of compensating patches. Preserve a checkpoint before
uncertain construction. A blocked attempt requires a changed, scoped strategy; exhausted or
uncertain ledgers are blockers, not permission to rename the issue or replay an operation.

The optional budget gate measures additions and source retention on scoped batches/narrow
calls. Trusted Python remains unrestricted and growth is checked afterward. Without a policy,
authoring is `procedural_unbounded`. Count compliance is not proof of parametric behavior,
simple topology, aesthetics or manufacturing readiness. Deleted/flattened history cannot
produce a maintainability pass; isolated replacement/promotion remains a separate review.

Wrap potentially long native calls with `ctx.native_call` (or `ctx.operation`) and meaningful
entity identity. Worker heartbeat means the worker is alive, never that Fusion completed a
Boolean. Cancellation is cooperative. Preserve completed stages and reconcile uncertain work;
never resubmit completed mutations because a wrapper failed. Flush engineering values with
`ctx.record` before optional presentation. Use `ctx.capture(required=False)` or read-only
`ctx.present` for nonessential images. Separate execution, regeneration, integrity, boundary,
exports, engineering evidence, authoring, readiness and caller approval.

Use compact replies and immutable report pages. Missing or omitted details never mean pass.
Do not weaken writer fingerprints or protected checks to save response bytes. Generated new
model dimensions need native creator/component attribution. Revision propagation can only be
cleared by the implemented bounded history-free B-rep control; authored history or unavailable
ownership stays unproven. Volume equality alone never establishes shape equivalence.

Manufacturing readiness still requires actual exported representation and slicer evidence.
Boolean kept-tool attribution, finite roots/ligaments, actual support paths, effective presets
and physical start enforcement are not newly implemented capabilities in 0.8.
