# Current review candidate: 0.8.0

Do not install this candidate yet. Follow [review/install/rollback](upgrade-v0.8-review.md) and its release condition. The earlier 0.7 authorization below is historical and does not authorize 0.8.

# Installation

Repository source is in [`software/fusion-prompt-mcp`](../software/fusion-prompt-mcp/). Copy that folder to your chosen permanent installation directory; the examples below assume `C:\AI-Make\fusion-prompt-mcp`. Do not point the MCP at the repository root.

## Existing installation

Follow [v0.7.0 upgrade and rollback](upgrade-v0.7.md). The update is available on `workbench`.
Both server and add-in must be updated together. Mauricio authorized this upgrade on 20 October 2026; preserve that authorization without inferring local completion. Downloading the
repository does not install the add-in or restart your MCP connection.

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


Current migration and rollback: [v0.7.0](upgrade-v0.7.md).
