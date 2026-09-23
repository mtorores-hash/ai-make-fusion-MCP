# Provenance and AI Make guideline review

## Imported source

- Package: Fusion-Prompt-MCP-v0.3.zip, produced earlier in this conversation.
- SHA-256: `2d41bc43b4473b577f1a32632467afcfed308fc253602fe67747c6f5546ed4d9`.
- Source copied unchanged into `software/fusion-prompt-mcp`; generated Python caches excluded.
- Original package README and CHANGELOG retained. Root docs reorganize the same technical facts
  and add navigation, current state, configuration, troubleshooting and evidence boundaries.
- Tool reference is generated from the 23 bundled server signatures/docstrings.
- Destination explicitly supplied by Mauricio: `mtorores-hash/ai-make-fusion-MCP`.

## Shared standards reviewed, 2026-09-22

AI_MAKE main was observed at `3a362de11fbedaba2acabf7d17b51e3feea34515` during this review.
Files were fetched from main; file blob hashes below identify the exact contents reviewed.

| File | Reviewed blob SHA |
| --- | --- |
| README.md | 2329f391841507767ffb799a410591d630c21600 |
| AGENTS.md | 924d45f6777d6d64b17cf76cf9c3bd1a1a918134 |
| AI_MAKE_AGENTS_WORKFLOW.md | 2818eca91091da566f02487385ee4fe8120d6a50 |
| CURRENT_LOCK.md | 5d6688840d699b10f4f86fd008ea0dfd75c68dce |
| ops/HANDOFF.md | f515a4b3144b7f2071a17499665235da8eef97fe |
| ops/DECISIONS.md | ff7171f9705409c3d2d8819e0101027a9aef7606 |
| REPO_LIBRARY.md | 31e6f14a9e72d202484ffb4e86cb8a4d29b3e2f4 |
| AI_MAKE_CHALLENGE_REPO_STANDARD.md | ccdd1c9cb21a7365f23d7c8249c1f9caec1d05a2 |
| AI_MAKE_CHALLENGE_LEDGER.md | 2076e23e51c1d5dbd7a3440e74cecc5b3e8d2ffc |
| AI_MAKE_AGENT_ENGINEERING_WORKFLOW.md | 7d7aaffda7bb18a99c77c9224a257b5a64077f39 |
| SYNC.md | f989ae0e16c0e17fd42b53ee9bbe8a648365b8ff |

## Applied decisions

- Use the user-designated project repo for engineering; AI_MAKE stores only routing and handoff.
- Keep unpublished work on workbench in the existing private repository.
- Use technical README/docs, software source, dependencies, examples and summarized tests.
- Keep CURRENT.md and ledger/LEDGER.md on workbench; keep main free of ledger/story content.
- Exclude runtime SQLite, credentials, footage, generated CAD outputs and third-party motor assets.
- Do not invent physical tests, challenge costs/time, episode publication or license grants.
- Preserve the existing active-challenge lock; this upload registers a supporting tool, not a new season.

The central standards remain authoritative. This record does not duplicate or replace them.

## v0.4 change provenance — 2026-09-23

Base workbench commit: f47c5bd191f889a033e2648636e1048d6ce31392 (v0.3 import).
New code is derived from that source and the supplied Pasted text.txt BRANCA lessons.
The package SHA above identifies the original v0.3 baseline, not the modified v0.4 source.
The requirements text is preserved in branca-lessons.md, with reported evidence distinguished
from this update's automated results. Current shared instructions were re-read before editing.

## v0.4.1 modeling-rule provenance

Base: 04da0ad5be0157538cb3bceb9afbabbf743d0e1d. The uploaded
Fusion-Parametric-Modeling-Best-Practices.md is preserved byte-for-byte under docs/.
Attachment SHA-256: `6a8a855d135d49ffd04706cbee141994fdac12173fceeac84d1973fabeeb8dd1`.
Operational interpretation is docs/modeling-rules.md, mirrored in the installable software and
verified by a regression test. The attachment's cited sources are the user's compilation;
this change does not represent an independent validation of every historical/community claim.
Primary API contracts used for inspection were checked; details in docs/modeling-hygiene.md.
