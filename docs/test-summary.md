# Current validation: 0.8.0 local development

177 software/API-double tests pass; new real STDIO/native acceptance unrun. See [current validation](k1-validation.md), [metrics](k1-response-metrics.json) and [register](k1-fix-disposition.json). The 0.7 results below are historical.

# Current validation: 0.7.0 development

159 tests pass (150 baseline plus 9 meaningful behavioral scenarios), syntax and diff checks pass. Native Fusion and real STDIO remain unrun. See [engineering-validation.md](engineering-validation.md) and [measured software evidence](engineering-metrics.json). These results do not prove production readiness.

## Historical v0.6 record

# Test summary — v0.6.0 development (2026-10-10)

**150 automated tests pass** on Python 3.12.14: 106 baseline tests first passed unchanged;
44 additional targeted regressions/source-contract checks now pass with the retained suite.
Tests use API doubles, temporary journals/files, numerical policies and source registration.
No Autodesk process or live design was accessed. No dependencies were installed.

| Verification | Result / evidence boundary |
| --- | --- |
| `python -m unittest discover -s tests -v` | 150 pass; final log included in review package |
| `python -m compileall -q software/fusion-prompt-mcp` | Pass; Python syntax only |
| Source registration and binding | 32 tool declarations, optional fields, observer default, resource/rules and example request binding checked with a lightweight registration stub; **not a real MCP schema/STDIO test** |
| Real `tests/check_mcp.py` | **Not run for v0.6**: MCP SDK absent; installation not authorized. Script updated for 32 tools/rules 1.1.0 and ready for existing installed environment |
| Rules/source integrity | Both rule copies identical; version/hash cache tested. Original supplied best-practices document unchanged against baseline |
| Patch and rollback | Forward applies to verified baseline; reverse returns original tree byte-for-byte; checks included in review package |
| Native Fusion/Windows/cloud | **Not run**. Separate approval required for disposable procedure |

New regressions cover scoped supplier exemptions and required interface evidence; stale/empty/
nonexistent/mismatched/descendant exports; new outside damage versus unrelated old findings;
frozen active components and added instances; after-failure narrow reports; native helper call
construction; conservative shared-instance/last-instance retirement and blockers; component-name
versus geometry evidence reuse; accepted older pins, actual state conflicts, observers and single-use
tokens; dirty assembly preservation with two sequential updates; uncertain saves, late completion,
wrong-version rejection and explicit reconciliation; linked experiment rejection before callbacks.

Remaining limitations:

- Real SDK serialization/schema compatibility and loaded Fusion APIs/kernel/solver/exports need validation.
- Scoped dependency sets are caller-reviewed. No complete projection/derive graph or automatic mechanical proof.
- Retirement is top-level non-derived leaf Remove only; native history/shared-instance behavior awaits acceptance.
- Bounded tasks detect arbitrary-Python changes afterward, with no rollback/sandbox or cross-document protection.
  New component definitions are rejected after bounded execution; prepare approved components beforehand.
- Component revision propagation can conservatively flag ancestor edits. BRep fingerprint supports conservative
  component-name reuse, not universal geometry equivalence, mesh/sketch-only reuse or arbitrary metadata immunity.
- Uncertain completion recovery requires an observed complete expected version plus caller verification. Failed
  uploads with no such version require manual recovery. Old v0.5 jobs have no retroactive uncertainty proof.
- Task/approval references are unauthenticated metadata; cloud operations do not enforce modeling member sets.
- No distributed locking, automatic joint/link migration, continuous collision proof or physical certification.

Current workbench was rechecked before packaging and still equals
`b15d491fe87fd4b1a1953ea148378f045f621f14`; all 57 original blobs were matched to its Git tree
before editing. The prepared changes were subsequently pushed to workbench with Mauricio's approval. No merge
to main, installation, live Fusion mutation, hardware action or AI_MAKE write occurred.

---

# Historical v0.5.0 evidence

**106 automated tests pass**. Coverage adds cloud API doubles for edit-token consumption,
dirty-to-dirty manual edits, stale/read-only/processing/other-editor rejection, reference
state, cloud checkpoints, first/in-place saves, upload futures/failures, duplicate operations,
restart interruption, dirty-document preservation and selected version updates.

Real STDIO MCP checks pass with **28 tools**, rules 1.0.5 tool/resource, schema validation,
persistent batch and cloud-job submission, deduplication and cancellation. Environment:
Python 3.12, MCP 1.30.0, declared dependency range unchanged. Syntax and identical rules
copies checked. No live Fusion cloud/kernel, Windows install or native geometry test here.

The decisive next check is [local Fusion acceptance](disposable-acceptance-v0.6.md):
manual edit/save of a named part, selected assembly-reference update, inspection and AI resumption.

## Historical v0.4.1 evidence


**80 automated tests pass** (63 retained + 17 hygiene tests). Real STDIO MCP checks pass:
25 tools, modeling-rules tool and resource with identical text, schema validation, persistent jobs,
operation-ID deduplication and cancellation. Protocol verification used Python 3.12 and MCP 1.30.0
within the existing declared dependency range. No dependency range was changed.

New fixtures check under-constrained sketches, yellow/red feature states, empty/default names,
root-body exceptions, sketch-size advisories, fixed-origin exclusion, fixed-entity review,
parameter metadata/dependency limitations, missing/null API data, direct-model preservation,
read-only grammar, checked-export refusal before file creation, required manual note and target-document
validation. Runtime and repository rule copies are compared in the repository test run.

These are numerical/API-double and real protocol tests, **not live Fusion kernel tests**.
Mauricio reported v0.4 running in Fusion; v0.4.1 is not installed or live-validated by this session.
Run [live hygiene acceptance](disposable-acceptance-v0.6.md) after updating.

---

## Historical v0.4 evidence

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
The attached source report describes prior native/custom-script results; its JSON files were
not available here, and those results are not evidence for the new wrappers. See
[lessons provenance](modeling-lessons.md) and [remaining work](upgrade-v0.4.md).

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
| Physical build / mechanical design | Not run | No manufacturing or mechanism result |

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


## 2026-10-20 adoption rerun

The reviewed 0.7 package was independently checked again: all 80 source hashes matched,
159 unit/source-contract/API-double tests passed, and compilation passed. Only supporting
installation/status documentation was adjusted for adoption. An isolated SDK installation
attempt failed because the execution environment could not resolve the package server;
real STDIO and Windows/Fusion/native/cloud checks remain unrun here. Do not mistake source
publication or these tests for installation. See CURRENT.md and upgrade-v0.7.md.
