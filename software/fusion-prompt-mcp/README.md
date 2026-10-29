# Fusion MCP 0.8.0

Local STDIO server and Autodesk Fusion add-in. 32 tools, caller contract 2.0, modeling rules 1.3.0.

This folder is the program. The repository [README](../../README.md) explains what it is, how to install it, and the limits of this prototype. Read that first.

- [Install](../../docs/installation.md)
- [Configuration](../../docs/configuration.md)
- [Caller contract](../../docs/caller-contract.md)
- [Tool signatures](../../docs/tool-reference.md)
- [Engineering checks](../../docs/engineering-contract.md)
- [Script helpers](../../docs/script-api.md)
- [Cloud workflow](../../docs/cloud-workflow.md)
- [Modeling rules](modeling-rules.md)

The add-in runs inside Fusion. `server.py` runs under the same account, on the same computer. The server needs Python 3.10+ and `mcp>=1.12,<2`. Fusion supplies its own `adsk` runtime.

Scripts are unrestricted Python. A failed script can leave a partial model. Cloud checks do not lock a file. Motion samples are not a continuous collision proof.

Automated tests do not start Fusion:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
```

With the MCP package installed, `python tests/check_mcp.py` talks to the server over STDIO and uses a temporary journal. It does not connect to Fusion.
