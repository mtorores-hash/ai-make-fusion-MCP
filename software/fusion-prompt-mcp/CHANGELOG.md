# v0.4.0 — 2026-09-23 (development)

BRANCA execution/verification slice: restricted read-only batches, explicit @root targeting,
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
