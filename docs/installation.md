# Installation

Repository source is in [`software/fusion-prompt-mcp`](../software/fusion-prompt-mcp/). Copy that folder to your chosen permanent installation directory; the examples below assume `C:\AI-Make\fusion-prompt-mcp`. Do not point the MCP at the repository root.

## Upgrade from v0.1 or v0.2

1. Save your Fusion document and stop FusionPromptBridge in Scripts and Add-Ins.
2. Back up the existing installation folder outside itself.
3. Extract this ZIP. Copy the contents of its `fusion-prompt-mcp` folder into the existing
   installation, replacing matching supplied files. Copy the ENTIRE `FusionPromptBridge`
   folder: `job_store.py`, `batch_runner.py` and `model_tools.py` are required.
   Keep `.venv` and your existing MCP configuration. Do not move the installation.
4. Restart Fusion to clear imported Python modules, then run FusionPromptBridge.
5. Restart the Fusion MCP connection in your desktop client.
6. Ask Codex to inspect the active design and call fusion_capabilities. It should report
   **0.3.0**, `batch_scripts: true`, and expose `run_model_script` plus `job_status`.

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

