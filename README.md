# AI Make Fusion MCP

A local MCP server and Autodesk Fusion add-in that let an AI client build and inspect native
Fusion models through typed tools or one complete Python modeling script.

## Current version and release status

**v0.7.0 development source on `workbench`, based on the reviewed package and baseline c0f7857. Windows installation is authorized but remains to be executed locally.** This is an unpublished supporting tool,
not a released or physically validated mechanical design. The repository remains private.
`main` is a landing page; no public release or episode milestone is asserted.

Read the [current-state gap analysis](docs/engineering-gap-analysis.md), [engineering interfaces](docs/engineering-contract.md) and [v0.7 installation/rollback](docs/upgrade-v0.7.md).

## Capabilities

- Fusion cloud projects, named parts, accepted version pins, separate observation/writer tokens and uncertain-save reconciliation.
- Selected-part validation/checked exports, caller edit boundaries and conservative native occurrence retirement.
- Full `adsk` batch scripts with explicit document/component targets and units.
- Durable jobs, operation-ID duplicate protection, progress, results, traceback and checkpoints.
- Sketch/extrude/fillet/joint tools plus nested assembly and geometry inspection.
- Geometry-based selection, interference and clearance checks, motion sampling.
- Declared continuity/access checks with revision-dependent evidence reuse, stage reconciliation and manufacturing declarations; native acceptance pending.
- F3D/STEP/STL export, print-copy orientation and exact-size PNG capture helpers.

The package exposes **32 MCP tools**. Full API access enables broader operations through
batch scripts; those operations are not all independently validated convenience tools.

## Hardware and software

A computer capable of running Autodesk Fusion; Windows is the documented installation path.
Fusion must be installed and open, with access sufficient to run its API add-ins.
The MCP process requires Python 3.10+ and `mcp>=1.12,<2`. Fusion uses its own Python runtime.
Both processes run under the same local account. A local STDIO-capable MCP client is required.
There are no custom electronics, firmware, fabrication files or physical BOM for this tool.

## Install and use

Start with [installation and upgrade](docs/installation.md), then [configuration](docs/configuration.md).
The complete reproducible software snapshot is in [software/fusion-prompt-mcp](software/fusion-prompt-mcp/).
Its original package README, dependency file, Windows setup helper, examples and tests are retained.

## Documentation

| Topic | File |
| --- | --- |
| Architecture, persistent jobs and recovery | [architecture](docs/architecture.md) |
| Script contract and helper API | [script API](docs/script-api.md) |
| All 32 tools and argument signatures | [tool reference](docs/tool-reference.md) |
| Geometry and feature-boundary selection | [geometry selection](docs/geometry-selection.md) |
| Validation method and live acceptance | [validation](docs/validation.md) |
| Evidence and test limits | [test summary](docs/test-summary.md) |
| Known issues and recovery | [troubleshooting](docs/troubleshooting.md) |
| Requirements, capabilities and open limitations | [scope](docs/scope.md) |
| Source provenance and AI Make compliance | [provenance](docs/provenance.md) |
| Primary API sources | [references](docs/references.md) |

## Known limitations

Live Fusion/Windows loading, CAD-kernel behavior, exports, transforms and joint solving have
not been verified here. Scripts run as trusted unrestricted Python; component targeting is
not a sandbox. Cancellation is cooperative; failures can leave partial changes. Linked-design checkpoints require a clean completed cloud save and produce a version manifest,
not a self-contained F3D archive. Cloud/version checks are optimistic, not distributed locking. Motion checks
are discrete samples. Section helpers produce curves, not clipped-solid Section Analysis.

## License

**No project license has been selected.** This private import grants no new reuse license.
Confirm licensing before a public release; preserve dependency and third-party asset terms.
No proprietary motor models or other third-party CAD assets are included.

## AI Make videos

No MCP-specific published episode is recorded. General channel: [AI Make](https://www.youtube.com/@aimaketech).

## Working state

See [CURRENT.md](CURRENT.md). The working [ledger](ledger/LEDGER.md) belongs on `workbench` only.
Shared operating context is [AI_MAKE](https://github.com/mtorores-hash/AI_MAKE).

Latest: [v0.7 installation/rollback](docs/upgrade-v0.7.md), [caller contract 1.1](docs/caller-contract.md),
and [compatibility handoff](docs/compatibility-handoff-ai-make.md).

Source update pushed to `workbench` with approval. Not installed or native-Fusion tested.

Modeling standard: [rules](docs/modeling-rules.md) and [audit / checked-export behavior](docs/modeling-hygiene.md).

Shared editing: [cloud workflow and live acceptance](docs/cloud-workflow.md).
