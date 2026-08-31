## 1. @context Validation

- [ ] 1.1 Add `SCHEMAORG_CONTEXT_ALLOWLIST` frozen set to `linked_data_mapper/general_schema_org_mapper.py` (or a sibling module)
- [ ] 1.2 Implement `validate_jsonld_context(raw_json: str) -> None` raising mapping error for unknown contexts
- [ ] 1.3 Call validation in `HtmlJsonLdDataset.fetch()` before `rdflib.Graph.parse()`
- [ ] 1.4 Add unit tests: valid HTTPS context, valid HTTP context (normalized), mixed http/https, Bioschemas extension, unknown context error

## 2. Multi-Dataset Handling

- [ ] 2.1 Extend `_find_dataset_subject` → `_find_dataset_subjects` returning `list[Node]` (all `schema:Dataset` subjects in either http/https namespace)
- [ ] 2.2 Update `_map_graph` to iterate subjects and yield multiple `HarvestedArc` (one per Dataset)
- [ ] 2.3 Add unit test: single Dataset (existing behaviour preserved)
- [ ] 2.4 Add unit test: multiple Datasets on one page → multiple outputs
- [ ] 2.5 Add unit test: DataCatalog with hasPart → outputs only for member Datasets, not the Catalog itself
- [ ] 2.6 Add unit test: graph with no Dataset → mapping error

## 3. DataDownload Distribution Mapping

- [ ] 3.1 Extend `_create_assay_table` to iterate `schema:distribution` → `schema:DataDownload` resources
- [ ] 3.2 Add output column for each distribution with `contentUrl` as the Measurement output URI
- [ ] 3.3 Add `encodingFormat` as a Format comment column
- [ ] 3.4 Add unit test: single DataDownload → single output column
- [ ] 3.5 Add unit test: multiple DataDownload → multiple output columns

## 4. Documentation

- [ ] 4.1 Create `docs/schemaorg_mapping.md` with field tables (Dataset → Investigation, Study, Assay)
- [ ] 4.2 Document identifier cascade precedence rule
- [ ] 4.3 Document `@context` allowlist and extension mechanism

## 5. Validation

- [ ] 5.1 `uv run ruff format middleware/linked_data/`
- [ ] 5.2 `uv run ruff check middleware/linked_data/`
- [ ] 5.3 `uv run pytest middleware/linked_data/tests -v --tb=short`
