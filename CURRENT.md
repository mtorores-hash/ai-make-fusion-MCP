# Current state

Branch: `workbench`. Mauricio approved pushing the prepared update on 2026-10-10.
Based on verified workbench `b15d491fe87fd4b1a1953ea148378f045f621f14`.
Version: **0.6.0 development**, rules **1.1.0**, caller contract **1.0**, **32 tools**.

## Now

2026-10-10: implemented scoped validation/checked exports, role-aware hygiene and dependency
evidence; allowed/frozen edit boundaries; native leaf-occurrence retirement; observer/writer
separation, accepted pins, preservative dirty/stale sequential save/update path and uncertain
save reconciliation. Added component-owned driven circle helper and rules hash reuse.
Operational rules align minimum external fidelity, joining intent, milestone evidence and
finite sampled motion. Original supplied best-practices source preserved.

## Evidence and limits

150 unit/source-contract tests pass (106 baseline first passed unchanged); syntax and rules
consistency checked. New real STDIO test is not run: MCP SDK absent and no install authorized.
API doubles do not establish loaded Fusion behavior. Native/cloud/Windows acceptance is pending.
Source update pushed to workbench with approval. No merge to main, AI_MAKE edits, installation,
live model changes or hardware operation performed.

## Next

Review the caller contract and installation/rollback instructions. Installation and disposable
native acceptance still need separate approval; pushing source does not deploy it to Fusion. See docs/upgrade-v0.6.md and docs/compatibility-handoff-ai-make.md.

## Open gates

Native APIs/kernel/cloud/exports and real MCP schema/STDIO; full dependency discovery, nested
retirement and bounded new-component authoring remain unsupported. Trusted Python is not
sandboxed, tokens are optimistic, and caller approvals are not authenticated.
