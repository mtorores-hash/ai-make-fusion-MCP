# Validation

Example files are in [`software/fusion-prompt-mcp/examples`](../software/fusion-prompt-mcp/examples/). Run development commands from `software/fusion-prompt-mcp`. Live acceptance is **pending**, not a reported pass.

## BRANCA examples and live acceptance

- `examples/parametric_spring_cup.py`: constrained annular sketch, named diameter/wall/height,
  change-and-restore diameter check, geometric selection, exports and exact-size screenshot.
  It is an integration test part, not the finished spring cup or extruder.
- `examples/inspect_existing_assembly.py`: full topology report saved as JSON.
- `examples/motion_check_template.py`: substitute inspected joint/body/occurrence references,
  sample an idler's swing and save 1920×1080 frames. It contains intentional placeholders.

Live gate on your PC:

1. Open a COPY of a local native design. Inspect version/document/component references.
2. Submit the spring-cup example once with units mm. Verify constraints, diameter-driven
   geometry updates, native timeline and exported files. Open the checkpoint separately.
3. Repeat the IDENTICAL request/operation ID. Confirm the same job ID and no duplicate part.
4. Run full inspection on a nested assembly; compare occurrence poses, body dimensions and
   selected edge/face references against Fusion. Confirm repeat instances are distinct.
5. Test a known overlapping pair and a known separated pair. Compare reported distance and
   interference volume against Fusion measurements. Zero clearance alone is not proof of
   non-interference. Unsupported API states must be errors, never “clear.”
6. Drive a test hinge/slider across known positions. Compare transforms/limits and confirm
   the original pose is restored even when a check fails or cancellation is requested.
7. Verify print-oriented exports against the source, cleanup of temporary copy, appearances,
   and actual PNG dimensions. Section curves are checked separately from presentation.
8. Test checkpoint failure, an intentional script error and bridge restart during a test job.
   Confirm full traceback, partial results, interrupted state and NO replay.

Nut insertion, clip removal, screwdriver access and the complete idler swing require
explicit tool/part clearance envelopes and defined paths. Discrete pose samples do not
prove continuous collision freedom. The connector provides measurements; it does not
infer or certify all mechanical access conditions automatically.

## Development verification

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python tests/check_mcp.py
python -m compileall -q .
```

MCP SDK is bounded to major version 1, not completely dependency-locked. No OpenAI API key
is required by this server: your connected Codex client supplies the model interaction.

