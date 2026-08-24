## 1. Harvest-source identifier chain (mapper)

- [x] 1.1 Add `_extract_all_dois(graph, subject) -> list[str]` and `_pick_canonical_doi(dois) -> str | None` (lexicographic `casefold` minimum)
- [x] 1.2 Add `harvest_source_id` on `UrlDiscoveryResult`; MyCoRe Solr sets Solr `id`; mapper resolves harvest source id before sanitized URL
- [x] 1.3 Implement `_plan_investigation_identifier` harvest-source-first chain (source URL → graph URL → DOI last resort)
- [x] 1.4 Emit `Alternate Identifier` Comments for non-canonical DOIs on the same page; keep canonical DOI in Publication
- [x] 1.5 Keep `LinkedDataMapper.map_graph(graph, source_url=...)` without collision context

## 2. Plugin (unchanged flow)

- [x] 2.1 Pass discovered page URL as `source_url` and optional `harvest_source_id` from `UrlDiscoveryResult` into `map_graph`

## 3. Unit tests

- [x] 3.1 Multi-DOI fixture with `source_url`: identifier = RDI id; alternate DOI in Comment; stable under permuted JSON-LD
- [x] 3.2 Same PANGAEA DOI on two Receive-URLs → distinct RDI identifiers; DOI in metadata only
- [x] 3.3 Single DOI without `source_url`: identifier = DOI; no spurious `Alternate Identifier`
- [x] 3.4 Generic `source_url` without RDI catalog id: sanitized page URL as identifier
- [x] 3.5 Sorcering pair: distinct harvest identifiers per page

## 4. Documentation

- [x] 4.1 Update Key Decisions in [`openspec/specs/linked-data-mapper/design.md`](openspec/specs/linked-data-mapper/design.md) for harvest-source-first policy

## 5. Validation

- [x] 5.1 `uv run ruff format middleware/linked_data/`
- [x] 5.2 `uv run pytest middleware/linked_data/tests/unit/test_mapper.py middleware/linked_data/tests/unit/test_linked_data_plugin.py -v`
