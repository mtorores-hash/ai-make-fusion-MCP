# Current state

Updated: 2026-09-22. Branch: `workbench`. Version: v0.3.0 development snapshot.

## Now

The tool documentation and matching software source are imported into the user-designated
private repository. No code behavior changes were part of this documentation import.
This is a supporting CAD automation tool; no new challenge budget, clock or episode is locked.

## Last experiment / evidence

Prior build in this conversation: 40 automated tests and real MCP protocol checks passed.
Tests cover SQLite/job behavior, geometry-selection predicates, dispatcher reentry and API
contracts using Fusion doubles. Real Fusion geometry and Windows add-in execution remain
unverified. See docs/test-summary.md for the evidence boundary and reproducible commands.

## Next question

Can the installed v0.3 bridge complete the parametric spring-cup example in a COPY of a local
Fusion design, produce a usable F3D checkpoint, and return the same job for an identical
operation ID? Run this live acceptance before using it for a full BRANCA extruder batch.

## Files touched

Repository README, AGENTS, .gitignore, CHANGELOG, docs/, source snapshot under software/,
CURRENT.md and ledger/LEDGER.md. Shared AI_MAKE receives the repo-library pointer and handoff.

## Open gates

Live Fusion acceptance; project license selection before any public release; episode/public
release authorization where applicable. No public release or repo visibility change performed.
