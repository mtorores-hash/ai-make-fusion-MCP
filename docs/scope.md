# Scope and capability map

This is a supporting tool for prompt-driven CAD. No BRANCA mechanism geometry, motor model,
challenge budget, validated physical fit or production readiness is included.

| Requested capability | v0.3 implementation | Evidence / boundary |
| --- | --- | --- |
| Batch script execution | Full trusted adsk script via durable jobs | Persistence/protocol tested; Fusion execution needs live acceptance |
| Full assembly inspection | Component definitions, nested occurrences, bodies, optional topology, dimensions, transforms, feature health | Implemented; real nested geometry validation pending |
| Constrained parametric sketches | Full API access and diameter-driven spring-cup example | Example is not a live-tested finished part |
| Broader modeling | Full adsk available for revolve, sweep, loft, patterns, split and other features | Not separate tested wrappers for every operation |
| Components and joints | Typed basic joints; script helpers for STEP import, joint limits and position sampling | Existing native design context required; solving pending |
| Geometry checks | Distance, interference, section-curve sketch and discrete motion samples | No automatic access-envelope or continuous-collision proof |
| Save/export/presentation | F3D/STEP/STL, temporary print-copy orientation, appearances, camera and PNG capture | Native Fusion output validation pending; no encoded video or cloud save management |

The script runner was explicitly requested after the earlier typed-tool-only versions. It
executes unrestricted local Python with user permissions. Target checks are guardrails, not
security isolation. Scripts must identify stage checkpoints and cooperative cancellation points.

Remaining gates are live Fusion validation and project license selection. A future public
release must follow AI Make's reviewed-engineering and publication rules. No GitHub release,
tag, repo visibility change or challenge-story material is part of this import.

## v0.4 update

See [BRANCA verification contracts and remaining work](upgrade-v0.4.md) for the latest behavior.
