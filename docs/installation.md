# Installation

Repository source is in [`software/fusion-prompt-mcp`](../software/fusion-prompt-mcp/). Copy that folder to your chosen permanent installation directory; the examples below assume `C:\AI-Make\fusion-prompt-mcp`. Do not point the MCP at the repository root.

## Upgrade from v0.1, v0.2, v0.3 or v0.4

1. Save your Fusion document and stop FusionPromptBridge in Scripts and Add-Ins.
2. Back up the existing installation folder outside itself.
3. Download the `workbench` branch (Code → Download ZIP). Copy the contents of
   `software/fusion-prompt-mcp` into the existing
   installation, replacing matching supplied files. Copy the ENTIRE `FusionPromptBridge`
   folder: all supplied Python modules are required, including `execution_policy.py`,
   `verification.py`, `experiments.py` and `design_intent.py`.
   Keep `.venv` and your existing MCP configuration. Do not move the installation.
4. Restart Fusion to clear imported Python modules, then run FusionPromptBridge.
5. Restart the Fusion MCP connection in your desktop client.
6. Ask Codex to inspect the active design and call fusion_capabilities. It should report
   **0.4.1**, `batch_scripts: true`, and expose `run_model_script` plus `job_status`.

These steps update your PC; the hosted development session has not modified that PC.

## Fresh Windows installation

Extract to `C:\AI-Make\fusion-prompt-mcp`. Install Python 3.10+ and run in PowerShell:

```powershell
cd C:\AI-Make\fusion-prompt-mcp
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

In Fusion's Scripts and Add-Ins dialog add the existing `FusionPromptBridge` folder and
run it. In your desktop client's local STDIO MCP settings use:

- Command: `C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe`
- One argument: `C:\AI-Make\fusion-prompt-mcp\server.py`

Equivalent Codex config entry (merge with existing config, do not replace it):

```toml
[mcp_servers.fusion]
command = 'C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe'
args = ['C:\AI-Make\fusion-prompt-mcp\server.py']
tool_timeout_sec = 45
```

Both processes run natively on the Fusion PC under the same OS account. Only one Fusion
instance can own the bridge; an OS lock enforces this. Hosted browser/mobile chats and
WSL/container environments do not share this local connection automatically.


See [v0.4 migration and coverage](upgrade-v0.4.md), particularly the new required motion-transform expectations.

For v0.4.1, copy `modeling-rules.md` beside server.py and all add-in modules, including
`hygiene.py` and `modeling_rules.py`. Restart both processes. Ask the client to call
`get_modeling_rules` and `audit_modeling_hygiene` before continuing native modeling.

For rules 1.0.1, refresh the complete software folder and restart both processes. The bridge
still reports runtime 0.4.1; get_modeling_rules and fusion_capabilities should report rules 1.0.1.
