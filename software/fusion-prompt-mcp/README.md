# Fusion Prompt MCP — 0.6.0 development

Local STDIO server plus main-thread Autodesk Fusion add-in. 32 tools, caller contract 1.0,
modeling rules 1.1.0. Update both processes together. No live installation or CAD acceptance
was performed for this change set.

- [Install and rollback](../../docs/upgrade-v0.6.md)
- [Caller contract, migration and limitations](../../docs/caller-contract.md)
- [Exact tool signatures](../../docs/tool-reference.md)
- [Script helpers](../../docs/script-api.md)
- [Cloud workflow and recovery](../../docs/cloud-workflow.md)
- [Operational modeling rules](modeling-rules.md)
- [Disposable native acceptance — approval required](../../docs/disposable-acceptance-v0.6.md)
- [Tests and remaining limitations](../../docs/test-summary.md)

The bridge must run on the Fusion computer under the same account as server.py. Python
3.10+ and existing mcp>=1.12,<2 are required by the server; Fusion provides its own adsk
runtime. No dependency change is needed from v0.5. Read-only observations no longer
implicitly acquire writer tokens. Scripts remain trusted unrestricted Python; no sandbox,
distributed locking, forced cancellation, automatic CAD rollback or mechanical certification.

Automated tests (no Fusion, no installation):

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
```

With an already installed MCP SDK, `python tests/check_mcp.py` checks real STDIO using a
temporary journal. It never connects to Fusion. It was not run in this update because the
SDK was absent and installing dependencies was not authorized.
