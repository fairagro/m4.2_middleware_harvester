## 1. Wrap and call scaffolding

- [ ] 1.1 Override `RegalMapper._stable_wrap` with `label_predicates=(SKOS.prefLabel,)` (no Schema.org term namespaces)
- [ ] 1.2 Introduce per-call `_RegalRun` (or equivalent) owning `stable`; stop ignoring `stable` in `_map_graph`
- [ ] 1.3 Pass `ResourceView` / `stable` into mapping helpers instead of raw `Graph` for ARC-bound reads

## 2. Port field access and delete helpers

- [ ] 2.1 Port title, description, dates, DOI, license, simple comments, spatial/collection/processing tables to `text` / `texts` / `labelled` / `resources`
- [ ] 2.2 Port contacts (sorted resources + labelled prefLabel) and publications / associatedPublication / OAI paths
- [ ] 2.3 Port `_funding_values` (joinedFunding preference + flat fallbacks) onto child ResourceViews
- [ ] 2.4 Port opaque comments: filter `_KNOWN_PREDICATES`, resolve object text via StableGraph, emit in deterministic order
- [ ] 2.5 Delete `_str`, `_strs`, `_term_text`, `_labelled_nodes`, `_join_literals`; grep-gate remaining ARC-bound `graph.value` / `str(BNode)` uses

## 3. Tests

- [ ] 3.1 Keep / adjust existing Regal funding-BNode and opaque-comment stability tests under ResourceView
- [ ] 3.2 Add creator/contributor order-permutation + double-map Contact stability test
- [ ] 3.3 Add opaque unknown-predicate order-permutation test
- [ ] 3.4 Add concurrent `map_graph` on one shared `RegalMapper` cross-talk guard (mirror Schema.org)

## 4. Validation

- [ ] 4.1 `uv run ruff format middleware/linked_data/` and `uv run ruff check` on affected package
- [ ] 4.2 `uv run pytest middleware/linked_data/tests/unit/test_regal_mapper.py middleware/linked_data/tests/unit/test_mapper.py -v`
- [ ] 4.3 `openspec validate --change migrate-regal-resource-view --strict`
