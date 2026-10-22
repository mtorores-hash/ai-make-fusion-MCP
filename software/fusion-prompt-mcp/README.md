# 0.8.0 development candidate — not deployed

Caller 2.0, rules 1.3.0, 32 tools. See [migration](../../docs/k1-caller-migration.md), [validation](../../docs/k1-validation.md) and [review/install/rollback](../../docs/upgrade-v0.8-review.md). Older installation authorization does not authorize this candidate.

# Fusion Prompt MCP — 0.7.0 development

Local STDIO server plus main-thread Autodesk Fusion add-in. 32 tools, caller contract 1.1,
modeling rules 1.2.0. Update both processes together. No live installation or CAD acceptance
was performed for this change set.

- [Install and rollback](../../docs/upgrade-v0.7.md)
- [Caller contract, migration and limitations](../../docs/caller-contract.md)
- [Exact tool signatures](../../docs/tool-reference.md)
- [Declared engineering checks and handoff](../../docs/engineering-contract.md)
- [Reward Rocket gap analysis and limits](../../docs/engineering-gap-analysis.md)
- [Script helpers](../../docs/script-api.md)
- [Cloud workflow and recovery](../../docs/cloud-workflow.md)
- [Operational modeling rules](modeling-rules.md)
- [Disposable native engineering acceptance](../../docs/engineering-validation.md)
- [Tests and remaining limitations](../../docs/test-summary.md)

The bridge must run on the Fusion computer under the same account as server.py. Python
3.10+ and existing mcp>=1.12,<2 are required by the server; Fusion provides its own adsk
runtime. No dependency change is needed from v0.6. Read-only observations no longer
implicitly acquire writer tokens. Scripts remain trusted unrestricted Python; no sandbox,
distributed locking, forced cancellation, automatic CAD rollback or mechanical certification.

Automated tests (no Fusion, no installation):

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
```

With an already installed MCP SDK, `python tests/check_mcp.py` checks real STDIO using a
temporary journal. It never connects to Fusion. It was not run in this update because the
SDK was absent; a later isolated SDK installation attempt could not resolve the package server. Run it with the existing local installation environment.
