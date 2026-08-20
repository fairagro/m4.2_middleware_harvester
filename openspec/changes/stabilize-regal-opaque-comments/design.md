## Context

See proposal.md for motivation. Today `RegalMapper._add_opaque_comments` walks every subject predicate not listed in `_KNOWN_PREDICATES` and, for non-Literal objects, appends `Comment(pred_name, skos:prefLabel or str(obj))`. Blank nodes without `prefLabel` therefore become Comment text equal to the parser-local blank-node id. `regal:contributorOrder` (`http://hbz-nrw.de/regal#contributorOrder`) is missing from `_KNOWN_PREDICATES` and is the observed Publisso failure mode. `_labelled_nodes` and a few OAI/funding helpers use the same `prefLabel or str(obj)` pattern and can leak blank-node labels into Comments or labels if those paths encounter unlabelled blank nodes.

## Goals / Non-Goals

**Goals:**

- Harvest-stable Regal Investigation Comments for Publisso/Regal records that carry `contributorOrder` or other unlabelled blank-node opaque predicates.
- Keep Literals, URIRefs, and `skos:prefLabel`-labelled nodes as Comments.
- Align with `docs/regal_mapping.md`: `contributorOrder` is not opaque metadata to dump into Comments.

**Non-Goals:**

- Changes in `m4.2_advanced_middleware_api` or API hash ignore lists.
- Schema.org mapper / keyword work.
- DataHUB CI changes.
- Implementing full Contact reordering via `contributorOrder` unless order keys are clearly stable Literals/URIRefs with little extra code; otherwise leave a TODO.

## Decisions

1. **Add `REGAL.contributorOrder` to `_KNOWN_PREDICATES`**
   — Reasoning: cheapest correct fix for the known Publisso noise; matches the mapping doc intent that this predicate is structural metadata, not an opaque facet. Alternative: only skip inside `_add_opaque_comments` by name — rejected because other known predicates are already centralized in the set.

2. **Skip unlabelled blank nodes everywhere opaque/label fallbacks exist; never `str(BNode)`**
   — Reasoning: blank-node labels are parser IDs, not domain values. Applying the rule only to `contributorOrder` would leave the same bug for the next unknown predicate. Touch `_add_opaque_comments` first; mirror the guard in `_labelled_nodes` / OAI / funding label fallbacks that use `prefLabel or str(obj)` so those paths cannot reintroduce the leak.

3. **Defer Contact ordering unless trivial and stable**
   — Reasoning: Publisso stability does not require ordering to stop `ARC_UPDATED`. Ordering needs a reliable key (ORCID / agent URI / literal pipe-string). If the live graph only offers blank-node membership without stable keys, ordering is a follow-up. Implementation SHOULD attempt a quick read of Literal/URIRef order values; if none are available, skip and document a TODO referencing `docs/regal_mapping.md`.

4. **Prove stability with unit tests, not production fixtures**
   — Reasoning: construct graphs with explicit `BNode()` objects; assert Comment sets contain no `N[0-9a-f]{32}` / `_:…` patterns and that two mappings with new blank nodes match.

## Risks / Trade-offs

- **Omitting unlabelled blank-node opaque facets drops some rare Comments** → accepted; those Comments were never meaningful harvest-stable metadata.
- **Existing ARCs that already contain `contributorOrder` blank-node Comments will change once** → first harvest after deploy removes the noisy Comment; subsequent harvests stay stable (intended).
- **Contact order may still differ from Regal display order until ordering is implemented** → accepted for this change; document follow-up.

## Migration Plan

- Deploy harvester only. No API or DataHUB migration.
- Rollback: revert `RegalMapper` change; blank-node Comment churn resumes.
