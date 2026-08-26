## 1. Harden Regal string helpers

- [x] 1.1 Change `RegalMapper._str` so Literals/URIRefs stringify as today; blank-node objects return `skos:prefLabel` or `None` (never `str(BNode)`)
- [x] 1.2 Change `RegalMapper._strs` to the same object policy (Literal / URIRef / BNode→prefLabel / skip); keep list semantics for multi-valued predicates
- [x] 1.3 Quick audit of remaining `str(obj)` / `str(value)` on graph nodes in `regal_mapper.py`; fix any path that can still emit blank-node labels into ARC fields

## 2. Tests

- [x] 2.1 Unit test: flat `fundingProgram` / `projectId` as BNodes without prefLabel → no `N[0-9a-f]{32}` / `_:…` in ARC JSON funding fields
- [x] 2.2 Unit test: flat (and/or joined) funding BNodes with `skos:prefLabel` → stable program/project/funder text present
- [x] 2.3 Unit test: two `map_graph` runs on the same logical funding-BNode fixture (fresh BNode identities) → identical Funding Program / Project ID / Funder strings
- [x] 2.4 Confirm existing joined-funding and opaque-comment tests still pass

## 3. Validation

- [x] 3.1 `uv run ruff format middleware/linked_data/` and `uv run ruff check` on affected paths
- [x] 3.2 `uv run pytest middleware/linked_data/tests/unit/test_regal_mapper.py -v`
- [x] 3.3 `openspec validate stabilize-regal-funding-bnodes`
