# v0.4.1 — Modeling hygiene (development)

## Unreleased — hardware sourcing rules (2026-09-27)

Rules 1.0.1 require online commercial CAD search, then asking the user, then specification-based
reconstruction before placeholders. Added sourcing/fidelity to manual audit review; runtime stays v0.4.1.

## Unreleased — documentation cleanup (2026-09-27)

Generalize project references and spring-cup parameter names; shorten modeling lessons to
reusable requirements. Runtime behavior and version unchanged. Original context remains in Git history.

Preserve Mauricio's supplied parametric modeling standard; ship operational rules with the
installation and expose them through a tool and MCP resource. Add a read-only whole-design
hygiene audit and explicit checked-export gate, with unknown-data and manual-review boundaries.
25 MCP tools. No forced changes to geometry, existing exports or recovery checkpoints.
Live Fusion acceptance pending; v0.4 installation reported running by Mauricio.

# v0.4.0 — 2026-09-23 (development)

Execution/verification slice: restricted read-only batches, explicit @root targeting,
bounded synchronization, independently verified motion poses/restoration, bounded adaptive
sampling, conservative root-body broad phase, disposable F3D experiments, dimensional tolerance
budgets, semantic selectors, surface review candidates, release hash/revision validation and
inclusive timing breakdown. Default modeling idempotency remains compatible with v0.3.

Breaking helper change: sample_motion now requires expected_world(position). No live Fusion
validation for v0.4. Full layer/slicer audit, primitive library and media timeline remain pending.

# v0.3.0

- Added persistent full-adsk Python batch jobs with explicit document/component/units.
- Added SQLite operation-ID duplicate protection, independent status/results, cooperative
  cancellation, exclusive bridge ownership and interrupted-job recovery without replay.
- Added main-thread dispatcher reentry protection and default pre-script F3D checkpoint.
- Added structured created references, measurements, files/checksums, logs and full traceback.
- Added nested inspection, geometric/feature-boundary selection, interference and distance checks.
- Added script helpers for parameters, section curves, STEP import, joint limits/motion samples,
  print-copy export, appearances, camera and verified 1920x1080 PNG dimensions.
- Included parameter-driven spring-cup example, full-assembly report and motion-check template.
- Retained existing typed tools. Total: 23 MCP tools.
- Validation: 40 automated unit/integration tests (Fusion test doubles), real MCP protocol checks,
  and Python syntax checks. Live Fusion/Windows/CAD-kernel validation remains outstanding.
