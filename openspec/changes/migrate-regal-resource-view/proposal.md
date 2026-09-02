## Why

`#138` shipped StableGraph / ResourceView and migrated Schema.org; Regal only
got the `MappingContext` signature and still reads the raw graph via private
`_str` / `_strs` / `_labelled_nodes` helpers. `#144` patched the acute Publisso
funding BNode-label leak, but unsorted multi-value / contact / opaque-comment
paths can still churn ARC content hashes. Migrating Regal onto the shared access
API (issue `#147`) removes the second hygiene stack and makes harvest-stable
field access the default.

## What Changes

- Override `RegalMapper._stable_wrap` with Regal label policy (`skos:prefLabel`);
  stop ignoring the injected `StableGraph` in `_map_graph`.
- Port all ARC-bound Regal RDF reads to ResourceView (`text` / `texts` /
  `labelled` / `resources` / `object_text`); introduce a per-call run holder
  analogous to Schema.org’s `_SchemaOrgRun`.
- **Delete** Regal-private string hygiene helpers
  (`_str`, `_strs`, `_term_text`, `_labelled_nodes`, `_join_literals`) once
  call sites are migrated.
- Deterministic ordering for contacts, multi-value strings, labelled lists, and
  opaque Investigation Comments that affect hash-relevant ARC content.
- Add Regal order-permutation / double-map / concurrent shared-mapper tests
  aligned with Schema.org stability guards.
- Supersede `#144` helper-level contract: keep its regression tests; ownership
  of BNode-safe text moves to StableGraph.

### Non-goals

- New StableGraph opaque/unknown-predicate API (opaque walk stays mapper-local).
- Fixing Schema.org `subjects[0]` Dataset pick, or Regal ResearchData subject
  pick beyond today’s behaviour.
- Implementing `contributorOrder`-based Contact sorting.
- Changing `docs/regal_mapping.md` field rules (behavioural mapping parity;
  stability under permutation is the success bar, not bit-identity with today’s
  arbitrary rdflib order).
- Moving mappers to `middleware.payload` (`#140`).
- Archiving `stable-graph-resource-view` (separate housekeeping).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `regal-to-arc-mapping`: RegalMapper MUST use StableGraph / ResourceView for
  ARC-bound RDF field access; private string helpers MUST be removed; multi-value
  / contact / opaque-comment order MUST be harvest-stable.
- `linked-data-mapper`: RegalMapper MUST use ResourceView for RDF field access
  (parallel to the Schema.org requirement); concurrent `map_graph` on a shared
  RegalMapper MUST NOT cross-talk.

## Impact

- Code: `middleware/linked_data/.../regal_mapper.py`, unit tests under
  `middleware/linked_data/tests/unit/` (especially `test_regal_mapper.py`).
- Domains: `openspec/specs/regal-to-arc-mapping/`, `linked-data-mapper/`.
  (`stable-graph` main spec may land when `#138` is archived; this change does
  not invent that capability.)
- Ops: one-time Publisso ARC rehash possible where previous order was
  rdflib-arbitrary; subsequent harvests SHOULD stop churning solely due to
  mapper order / BNode labels.
- Tracks: GitHub `#147` (supersedes remaining `#144` hygiene debt).
