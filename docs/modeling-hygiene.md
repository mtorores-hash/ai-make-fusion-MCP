# Modeling hygiene — v0.6.0 / rules 1.1.0

The original supplied [best-practices document](Fusion-Parametric-Modeling-Best-Practices.md)
is unchanged source material. Both copies of [modeling-rules.md](modeling-rules.md) are the
same active operational guidance. Retrieve with `get_modeling_rules(known_sha256='')`;
matching hash returns metadata without text, and the resource always returns full text.

Use [caller contract 1.0](caller-contract.md) for selected targets, relevant dependencies,
roles, maturity, lifecycle and required milestone evidence. Explicit scope checks current
revisions and excludes unrelated components with reasons. Untouched purchased/reference/
environment/envelope/fixture/presentation parts keep supplier naming and need sourced
interface-envelope evidence. Modified external geometry gets authored checks in batch audits.
Legacy omitted scope remains full-design authored checking and can report old supplier names.

Authored checks cover parametric history, default/empty names, sketch constraint/size/Fix,
feature/joint health, root-body review and declared parameter metadata/dependencies.
Unavailable API data fails completeness. Sketch-count/name-prefix thresholds are review
heuristics, not manufacturing policy. `strict_reviews=True` blocks review items as well.

Reports include `automated_checks_passed`, `inspection_complete`, applicable checks,
not-applicable items, exclusions, evidence gaps and scope revisions. Required checks missing
fresh evidence remain unproven; explicit not-applicable items never become passes or quality
waivers. `full_standard_verified` stays false. Geometry junction/functional fit, parameter
perturbation, valid references and physical properties still require the approved evidence.
Unchanged evidence may be reused only with complete dependency records; do not demand fresh
sections after cosmetic component renames.

`ctx.export_checked(...,scope=...)` regenerates and verifies the actual selected component/body,
new/relevant integrity, permitted edits and hygiene/evidence before writing. Nonempty manual
review note is required but is not authenticated approval. Parent exports must enumerate all
included descendants. Plain exports/checkpoints remain unchecked working/recovery routes.
Full signatures, fields and examples: [caller contract](caller-contract.md).
