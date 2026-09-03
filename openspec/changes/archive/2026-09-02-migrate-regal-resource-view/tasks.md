## 1. Wrap and call scaffolding

- [x] 1.1 Override `RegalMapper._stable_wrap` with `label_predicates=(SKOS.prefLabel,)` (no Schema.org term namespaces)
- [x] 1.2 Introduce per-call `_RegalRun` (or equivalent) owning `stable`; stop ignoring `stable` in `_map_graph`
- [x] 1.3 Pass `ResourceView` / `stable` into mapping helpers instead of raw `Graph` for ARC-bound reads

## 2. Port field access and delete helpers

- [x] 2.1 Port title, description, dates, DOI, license, simple comments, spatial/collection/processing tables to `text` / `texts` / `labelled` / `resources`
- [x] 2.2 Port contacts (sorted resources + labelled prefLabel) and publications / associatedPublication / OAI paths
- [x] 2.3 Port `_funding_values` (joinedFunding preference + flat fallbacks) onto child ResourceViews
- [x] 2.4 Port opaque comments: filter `_KNOWN_PREDICATES`, resolve object text via StableGraph, emit in deterministic order
- [x] 2.5 Delete `_str`, `_strs`, `_term_text`, `_labelled_nodes`, `_join_literals`; grep-gate remaining ARC-bound `graph.value` / `str(BNode)` uses

## 3. Tests

- [x] 3.1 Keep / adjust existing Regal funding-BNode and opaque-comment stability tests under ResourceView
- [x] 3.2 Add creator/contributor order-permutation + double-map Contact stability test
- [x] 3.3 Add opaque unknown-predicate order-permutation test
- [x] 3.4 Add concurrent `map_graph` on one shared `RegalMapper` cross-talk guard (mirror Schema.org)

## 4. Validation

- [x] 4.1 `uv run ruff format middleware/linked_data/` and `uv run ruff check` on affected package
- [x] 4.2 `uv run pytest middleware/linked_data/tests/unit/test_regal_mapper.py middleware/linked_data/tests/unit/test_mapper.py -v`
- [x] 4.3 `openspec validate --change migrate-regal-resource-view --strict`
