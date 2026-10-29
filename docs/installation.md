# Installation

Version 0.8.0. Install the server and the Fusion add-in from the same copy of [`software/fusion-prompt-mcp`](../software/fusion-prompt-mcp/). Update them together. The paths below are placeholders. Use any permanent folder you control.

## Windows

1. Copy `software/fusion-prompt-mcp` to `C:\AI-Make\fusion-prompt-mcp`.
2. Install Python 3.10 or newer, then in PowerShell:

```powershell
cd C:\AI-Make\fusion-prompt-mcp
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`setup-windows.ps1` creates that environment, installs `requirements.txt`, and writes `mcp-client-config.generated.toml` in the install folder. Do not commit the generated file.

3. In Fusion, open **Utilities > Scripts and Add-Ins**, add the existing `FusionPromptBridge` folder, and run it.
4. In your MCP client's local STDIO settings, set:

- Command: `C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe`
- One argument: `C:\AI-Make\fusion-prompt-mcp\server.py`

```toml
[mcp_servers.fusion]
command = 'C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe'
args = ['C:\AI-Make\fusion-prompt-mcp\server.py']
tool_timeout_sec = 45
```

Merge this block into the client configuration you already have. Replace the paths if you installed somewhere else.

Fusion and `server.py` run on the same computer, under the same Windows account. An operating-system lock lets one Fusion instance own the bridge. Reconnect the client after you change the server. Restart Fusion after you replace the add-in.

The server does not use an API key. See [configuration](configuration.md) for the job folder and the timeout.
