# Fusion MCP

Fusion MCP is a local [MCP](https://modelcontextprotocol.io) server and an Autodesk Fusion add-in. An AI agent can use it to drive Fusion for parametric CAD: inspect a design, build or change geometry, and check what it made, on your computer, through Fusion's own API.

Version 0.8.0. The server exposes 32 tools. The caller contract is 2.0 and the modeling rules are 1.3.0.

This is a prototype. It has not been thoroughly tested. You use it at your own risk. It can change a design, leave a model half-finished, or fail in ways the automated tests do not catch. Work on a copy of anything you care about.

## Requirements

- Autodesk Fusion, installed, open, and allowed to run add-ins.
- Windows for the install steps below. The add-in manifest also lists Mac, but those steps are not written out here.
- Python 3.10 or newer, on the same computer as Fusion.
- The Python package `mcp`, version 1.12 or newer and older than 2. Fusion uses its own Python. The server uses the environment you create below.
- Fusion and the MCP server running under the same Windows account. A browser chat or a remote container does not share this connection.
- An AI client that can start a local program and talk to it over standard input and output (STDIO).

## Install

Copy [`software/fusion-prompt-mcp`](software/fusion-prompt-mcp/) to a permanent folder. The examples use `C:\AI-Make\fusion-prompt-mcp`. Point the client at that folder, not at the root of this repository.

In PowerShell:

```powershell
cd C:\AI-Make\fusion-prompt-mcp
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`setup-windows.ps1` in that folder does the same install and writes `mcp-client-config.generated.toml` beside the script. That file is generated for your machine. Do not commit it.

In Fusion, open **Utilities > Scripts and Add-Ins**, choose **Add-Ins**, add the existing `FusionPromptBridge` folder, and run it. The server and the add-in are one version. Update them together. Only one Fusion session can own the bridge.

More detail is in [installation](docs/installation.md).

## Configure

Tell your MCP client to launch the server:

- Command: `C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe`
- Argument: `C:\AI-Make\fusion-prompt-mcp\server.py`

```toml
[mcp_servers.fusion]
command = 'C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe'
args = ['C:\AI-Make\fusion-prompt-mcp\server.py']
tool_timeout_sec = 45
```

Merge this into the client settings you already have. The server has no API key of its own. Your client signs in on its own. Nothing in this package listens on the network.

The 45-second timeout applies to a tool call that returns right away. A modeling script is queued. Poll `job_status` and `job_result` with the job id you got back.

Reconnect the client after you change the server path. Restart Fusion after you change the add-in. If the server and the add-in disagree, edits stop with `MCP_RUNTIME_MISMATCH` before they run.

Jobs, checkpoints, and output files are stored in `%USERPROFILE%\.fusion-prompt-mcp`. Older export helpers also write `%USERPROFILE%\FusionPromptExports`. Keep both folders out of git and off shared drives.

See [configuration](docs/configuration.md).

## Usage

1. Open Fusion and run the FusionPromptBridge add-in.
2. Connect the MCP client so it starts `server.py`.
3. Have the agent inspect the open design before it edits anything. It needs the current document id and component token.
4. For a change, the agent takes an edit token, names the document and component, and either calls a typed tool or submits one Python script with `run_model_script`.
5. Poll the job. Sending the same operation id and the same request returns the same job. After an interruption, inspect the model and the job before you try again.

Typed tools cover sketches, extrudes, fillets, joints, inspection, and export. A script can use the rest of Fusion's `adsk` API. Sample scripts are in [`software/fusion-prompt-mcp/examples`](software/fusion-prompt-mcp/examples/).

| Topic | Document |
| --- | --- |
| Install | [docs/installation.md](docs/installation.md) |
| Configuration | [docs/configuration.md](docs/configuration.md) |
| Tools | [docs/tool-reference.md](docs/tool-reference.md) |
| Scripts | [docs/script-api.md](docs/script-api.md) |
| Caller contract | [docs/caller-contract.md](docs/caller-contract.md) |
| Modeling rules | [docs/modeling-rules.md](docs/modeling-rules.md) |
| Cloud saves | [docs/cloud-workflow.md](docs/cloud-workflow.md) |
| Limits of the tool | [docs/scope.md](docs/scope.md) |
| When something fails | [docs/troubleshooting.md](docs/troubleshooting.md) |

## Limitations

- Prototype. Automated tests use stand-ins for Fusion. Live Fusion, cloud saves, crashes, and physical parts have not been fully exercised. Use it at your own risk.
- Scripts are unrestricted Python. They run with your account's permissions, inside Fusion, on the main thread.
- Cancellation is cooperative. A Fusion kernel call or a tight Python loop keeps running until it returns.
- A failed or cancelled script can leave the model partly changed. There is no automatic undo of a finished feature.
- Cloud version checks notice conflicts. They do not lock the file against another editor.
- Motion checks are samples at chosen poses. They do not prove that parts stay clear through the whole move.
- A checkpoint of a linked cloud assembly is a list of saved versions, not a single self-contained F3D file.
- The tool does not certify a design for manufacturing, printing, or fit.

## License

This software is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).

You may use, change, and share it for noncommercial purposes, under the terms in `LICENSE`. Mauricio Toro keeps all commercial rights. Commercial use needs a separate license from Mauricio Toro.

Required Notice: Copyright 2026 Mauricio Toro. All commercial rights reserved.

## Contributing

Read [PUBLIC-REPO-RULES.md](PUBLIC-REPO-RULES.md) before you add a file. Internal project material stays in the private AI_MAKE repository.
