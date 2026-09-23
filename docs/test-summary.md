# Test summary — v0.4.0

2026-09-23: **63 tests pass**, plus the real STDIO MCP protocol check (23 tools).
New coverage: repeated read-only batches perform no regeneration; modeling still regenerates;
read-only mutation/escape attempts are rejected; default v0.3 idempotency preserved; explicit root;
stale world transform rejected despite matching joint value; pose restored on measurement error;
destructive volume/envelope/protected-interface changes rejected; candidate lifecycle closes unsaved;
semantic re-resolution rejects ambiguity; small functional edges remain review candidates;
nominal-clear/tolerance-failing fixture; bounded narrow-contact refinement with unresolved intervals;
stale revision/calculation/hash rejected.

Commands from `software/fusion-prompt-mcp`:

```sh
python -m unittest discover -s tests
python tests/check_mcp.py
```

These are numerical, filesystem, real transport and Fusion API-double tests. **No v0.4 live
Windows/Fusion kernel, archive, joint solver or physical print validation was performed.**
The attached BRANCA report describes prior native/custom-script results; its JSON files were
not available here, and those results are not evidence for the new wrappers. See
[lessons provenance](branca-lessons.md) and [remaining work](upgrade-v0.4.md).

---

## Historical v0.3 evidence (unchanged below)

# Test summary — v0.3.0

## Objective

Check connector behavior and failure handling before attempting live native CAD automation.

## Configuration

Source matches the v0.3 package identified in provenance.md. Python tests ran in the hosted
Linux build environment during the preceding implementation in this conversation, on
2026-09-22. Fusion itself was unavailable. This documentation import changes no runtime code.

## Method

Tests use real temporary files and SQLite transactions for transport, job persistence and
concurrency. Fusion behavior is represented by API doubles for the batch engine, geometric
predicates, joint/fillet dispatch and custom-event handler contracts. A real MCP client starts
the server over STDIO for protocol, schema and job lifecycle checks.

## Recorded results

| Check | Observed result | What it establishes |
| --- | --- | --- |
| Unit/integration suite | 40 tests passed | Tested transport, persistence and API contracts |
| Concurrent identical submissions | One job ID | Duplicate-operation rejection under tested concurrency |
| Interrupted-job recovery | No replay | Running jobs become interrupted |
| Wrong target / failed checkpoint | Script rejected before execution | Tested guard ordering |
| Cooperative cancellation | Passed | Cancellation at an explicit boundary |
| Custom-event handler reentry | Passed | Tested handler serialization |
| Real MCP protocol check | Passed; 23 tool schemas | Initialization, schema validation, queue/status/cancel and duplicate behavior |
| Python syntax | Passed | Packaged Python files compile |
| Fusion kernel / Windows add-in | Not run | No live CAD validity or installation claim |
| Physical build / BRANCA extruder | Not run | No manufacturing or mechanism result |

## Reproduce

From `software/fusion-prompt-mcp` after installing requirements:

```sh
python -m unittest discover -s tests -v
python tests/check_mcp.py
python -m compileall -q .
```

## Conclusion and limitations

The recorded tests support a development snapshot suitable for live acceptance work. They do
not prove Autodesk API compatibility, CAD topology correctness, nested coordinate transforms,
checkpoint recoverability, file export quality, joint solving, continuous collision clearance,
or printability. Test doubles can reproduce assumptions that the real API may reject.

Run [the live acceptance sequence](validation.md) on a copy of a local Fusion model. Record
Fusion version, Windows version, actual outputs and failures before promoting release claims.
Documentation checks for this import verify local links, exact source/package correspondence,
23 generated tool entries and excluded-runtime-file rules; they are not new CAD tests.
