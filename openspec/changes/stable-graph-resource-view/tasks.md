## 1. StableGraph API

- [ ] 1.1 Add `linked_data_mapper/stable_graph.py` with `StableText`, `ResourceView`, `LabelledNode`, wrap/policies (label predicates, schema.org http/https aliases)
- [ ] 1.2 Implement literal / literals (language preference `en` > `de` > untagged > other; empty drop; stable plural dedupe/sort)
- [ ] 1.3 Implement resource / resources (deterministic IRI / BNode content-signature order; optional `of_type`)
- [ ] 1.4 Implement `labelled`, `doi` (Literal / IRI / Schema.org PropertyValue), `http_iri`
- [ ] 1.5 Add unit tests for BNode skip, language preference, deterministic picks/lists, `doi` PropertyValue, `labelled`, dual schema.org namespaces
- [ ] 1.6 Add shared test helper `assert_harvest_has_no_bnode_labels` (extend `mapper_test_helpers.py`)

## 2. MappingContext ABC

- [ ] 2.1 Add frozen `MappingContext` (`source_url`, `harvest_source_id`) beside the mapper ABC
- [ ] 2.2 Change `LinkedDataMapper.map_graph` to `map_graph(graph, context: MappingContext | None = None)`
- [ ] 2.3 Update `RegalMapper.map_graph` signature only (ignore context; no behaviour change)
- [ ] 2.4 Update plugin to build `MappingContext` from `UrlDiscoveryResult` and pass it to `map_graph`
- [ ] 2.5 Update plugin / mapper unit tests that assert `source_url` / `harvest_source_id` kwargs to use `MappingContext`

## 3. Schema.org migration

- [ ] 3.1 Wrap graph in StableGraph inside `GeneralSchemaOrgMapper.map_graph`; resolve Dataset subject as ResourceView
- [ ] 3.2 Replace `_str` / `_strs` / `_obj` / language / BNode-signature / `_schema_objects` / `_http_iri` / DOI PropertyValue helpers with ResourceView accessors (lift semantics)
- [ ] 3.3 Keep identifier cascade, sanitize, multi-DOI alternate comments, and publisher-invert logic in the mapper composed from API bricks + MappingContext
- [ ] 3.4 Delete obsolete private RDF-hygiene methods from `GeneralSchemaOrgMapper`
- [ ] 3.5 Confirm existing Schema.org tests (`test_mapper.py`, `test_mapper_identifier.py`) stay green; add/adjust only for MappingContext call sites

## 4. Validation

- [ ] 4.1 `uv run ruff format middleware/linked_data/` and `uv run ruff check middleware/linked_data/`
- [ ] 4.2 `uv run pytest middleware/linked_data/tests -v --tb=short`
