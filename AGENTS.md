# Agent instructions — AI Make Fusion MCP

Read README.md, CURRENT.md and ledger/LEDGER.md before editing this unpublished branch.
Follow the latest AI_MAKE README authority order and house workflow; current upstream rules
supersede this routing summary. See docs/provenance.md for the source revisions reviewed.

- Canonical tool repo: mtorores-hash/ai-make-fusion-MCP. Work on `workbench`.
- Source: software/fusion-prompt-mcp. Technical docs: docs/.
- Preserve existing Fusion native models. Generated models belong in their active project,
  not in this tool repository by default.
- No public release, visibility change or promotion to main is implied by a documentation update.
- Do not commit local job databases, submitted project scripts from runtime queues, artifacts,
  checkpoints, credentials, machine-specific configuration, footage or private CAD assets.
- Distinguish real MCP/filesystem tests, Fusion API doubles and actual Fusion kernel tests.
  Do not claim live Fusion validation from mocked tests.
- Update CURRENT.md and ledger/LEDGER.md after durable changes. Keep ledger off public main.
- Keep source and tool documentation aligned. Use the same operation ID after an uncertain
  batch submission; inspect interrupted jobs instead of silently replaying them.
- No new license, financial totals, challenge clock, physical test or release claim without evidence.

## Parametric modeling hygiene

Read docs/modeling-rules.md before modeling, and preserve the supplied reference in
docs/Fusion-Parametric-Modeling-Best-Practices.md. Runtime tools/resources expose the same
rules to installed clients. Component ownership, real driving parameters, named geometry,
constrained sketches and healthy features are required for new native parametric work.
Use the structured hygiene audit and explicitly review what it cannot prove. See
docs/modeling-hygiene.md for gate scope, legitimate exceptions and live acceptance.
Do not rename, convert or repair existing/imported hardware merely to obtain a clean report.

For all external parts, use the minimum functional source-grounded representation required by
the approved task. Supplier CAD is useful, but a drawing-derived envelope need not wait for
richer CAD once interfaces are known. Preserve provenance and unknowns; see docs/modeling-rules.md.

For PCB layout, default to connector/pin clearance volumes and cable routes to the correct
board area/orientation. Detailed connector/pin modeling requires an explicit user request;
use accurate sourced envelopes and preserve original supplier CAD. See modeling-rules.md.

For critical junctions, follow the junction-completeness rule: classify intent, verify local
attachment and thickness, and retain close-up/section evidence before completion. Healthy
features and a single solid are insufficient. This remains explicit manual review.

Choose physical connections before adding hardware. Consider consolidation, motion, loads,
service and assembly access; record a brief rationale per distinct connection and review
redundant/inaccessible fasteners. Follow the connection-selection rule in docs/modeling-rules.md.

Use Fusion cloud projects and named native part files for shared editing. Read
`docs/cloud-workflow.md`; preserve user edits, file IDs and links, use edit tokens before
mutations, and confirm completed cloud saves before handoff. Never silently migrate assemblies.

Use caller contract 1.1 in docs/caller-contract.md. MCP executes scoped operations; the caller owns
workflow approvals and external records. Review packages do not authorize push, installation or live CAD tests.

For the 2026-10-20 update, Mauricio explicitly authorized implementation and installation.
See CURRENT.md for the actual source/test/runtime states. Do not repeat a resolved approval
request, infer installation from a source push, or change AI Make model routing.
