# Troubleshooting

| Symptom | Check / next action |
| --- | --- |
| Old version or missing tools | Restart Fusion and the MCP process; verify both point to the upgraded folder and all add-in modules were copied. |
| Python cannot import mcp | Install requirements using the same `.venv` Python configured as the MCP command. |
| Unknown document/component | Inspect again. Document IDs are session-specific; component tokens are not occurrence tokens. |
| Job stays queued | Verify Fusion and the add-in are running under the same local account. A hosted chat cannot reach this queue automatically. |
| Job says waiting | Finish the active Fusion command/sketch/dialog. |
| Another bridge owns the queue | Stop the other Fusion add-in instance. Do not delete the job DB to bypass the lock. |
| Operation ID conflict | Same ID is only valid for an identical request. Inspect the earlier job before intentionally creating a new operation. |
| Interrupted after restart | Inspect partial geometry and result/checkpoint records. Do not replay automatically. |
| Cancellation stays running | Wait for a cooperative script boundary; kernel calls and infinite loops cannot be safely force-cancelled. |
| Checkpoint fails | No script code should have run. Inspect export support, linked components and file error details before proceeding. |
| Ambiguous geometry selection | Review candidate geometry or use Fusion selection. Never choose the first edge solely to bypass ambiguity. |
| Minimum distance is zero | Check interference separately; touching and penetration can both report zero distance. |
| Output file path is unavailable in cloud chat | It refers to the Fusion PC. Read it from that local environment or transfer it explicitly. |

Use job_result for the complete error traceback. Model changes can be partial after a failure;
open the last usable F3D checkpoint separately and inspect it. Automatic rollback is not supplied.
See architecture.md for state and restart behavior, and script-api.md for execution boundaries.

## v0.4 update

See [BRANCA verification contracts and remaining work](upgrade-v0.4.md) for the latest behavior.
