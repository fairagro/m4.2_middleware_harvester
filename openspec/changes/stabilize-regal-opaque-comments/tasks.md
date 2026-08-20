## 1. Mapper hardening

- [x] 1.1 Add `REGAL.contributorOrder` (`http://hbz-nrw.de/regal#contributorOrder`) to `_KNOWN_PREDICATES` in `regal_mapper.py`
- [x] 1.2 Change `_add_opaque_comments` so blank-node objects without `skos:prefLabel` are skipped; never append `str(BNode)`; keep Literals, URIRefs, and prefLabel texts
- [x] 1.3 Apply the same blank-node guard to `_labelled_nodes` and analogous OAI/funding `prefLabel or str(obj)` fallbacks so those paths cannot emit blank-node labels
- [x] 1.4 Optionally: if `contributorOrder` exposes stable Literal/URIRef order keys with little code, sort Creator/Contributor contacts accordingly; otherwise add a short TODO referencing `docs/regal_mapping.md` and leave contacts unordered by this predicate

## 2. Tests

- [x] 2.1 Add unit test: `contributorOrder` → blank node without prefLabel → no Comment named `contributorOrder` and no Comment text/`@id` matching `N[0-9a-f]{32}` or `_:…`
- [x] 2.2 Add unit test: two `map_graph` calls with freshly allocated blank nodes → identical Comment name/text sets (no `contributorOrder` noise)
- [x] 2.3 Add unit test: opaque unknown predicate + blank node without prefLabel → skipped
- [x] 2.4 Add unit test: opaque blank node with prefLabel → Comment kept with stable text
- [x] 2.5 Confirm existing Regal/Publisso tests still pass

## 3. Validation

- [x] 3.1 `uv run pytest middleware/linked_data -v --tb=short`
- [x] 3.2 `uv run ruff check` and `uv run ruff format --check` on changed files
