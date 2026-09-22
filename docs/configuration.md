# Configuration

Run the MCP server and Fusion under the same Windows account on the same computer.
Choose a permanent installation path; the executable and server paths must refer to that
installation. The repository root is not the executable source folder.

```toml
[mcp_servers.fusion]
command = 'C:\AI-Make\fusion-prompt-mcp\.venv\Scripts\python.exe'
args = ['C:\AI-Make\fusion-prompt-mcp\server.py']
tool_timeout_sec = 45
```

Merge this example with existing client configuration. It contains no credentials and does
not require an OpenAI API key. The connected AI client handles its own authentication.
No HTTP listener or network tunnel is part of this package.

The server exposes synchronous typed tools and asynchronous batch submission/status tools.
The 45-second client timeout is not a deadline for a queued batch job. Poll job_status and
job_result after run_model_script returns the durable job ID.

Runtime storage is under the OS user's `.fusion-prompt-mcp` directory, outside this repository.
It includes job SQLite state, operation requests, model checkpoints and output artifacts.
The legacy export tool writes to `FusionPromptExports` under the same user's home directory.
Keep both runtime locations out of Git and shared network folders.

No environment-variable configuration is currently exposed for relocating the shared job
queue. The server and add-in both use the same user's home directory. One Fusion instance
owns the queue at a time through an OS lock.

For a batch, obtain document/component references from a fresh inspection. Units must be one
of mm, cm, m or in. Named-parameter expressions should include units. Native adsk geometry
numbers continue to use Fusion's centimetres/radians.
