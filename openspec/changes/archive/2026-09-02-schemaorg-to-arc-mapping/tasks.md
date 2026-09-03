## 1. @context Validation

- [x] 1.1 Add `SCHEMAORG_CONTEXT_ALLOWLIST` frozen set to `linked_data_mapper/general_schema_org_mapper.py` (or a sibling module)
- [x] 1.2 Implement `validate_jsonld_context(raw_json: str) -> None` raising mapping error for unknown contexts
- [x] 1.3 Call validation in `HtmlJsonLdDataset.fetch()` before `rdflib.Graph.parse()`
- [x] 1.4 Add unit tests: valid HTTPS context, valid HTTP context (normalized), mixed http/https, Bioschemas extension, unknown context error

## 2. Multi-Dataset Handling

- [x] 2.1 Extend `_find_dataset_subject` → `_find_dataset_subjects` returning `list[Node]` (all `schema:Dataset` subjects in either http/https namespace)
- [x] 2.2 Update `_map_graph` to iterate subjects and yield multiple `HarvestedArc` (one per Dataset)
- [x] 2.3 Add unit test: single Dataset (existing behaviour preserved)
- [x] 2.4 Add unit test: multiple Datasets on one page → multiple outputs
- [x] 2.5 Add unit test: DataCatalog with hasPart → outputs only for member Datasets, not the Catalog itself
- [x] 2.6 Add unit test: graph with no Dataset → mapping error

## 3. DataDownload Distribution Mapping

- [x] 3.1 Extend Investigation + `_create_assay_table` to iterate
      `schema:distribution` → `schema:DataDownload` resources
- [x] 3.2 Add Investigation `"Distribution"` comments
      (`encodingFormat: contentUrl`, skip empty `contentUrl`)
- [x] 3.3 Add one Measurement `"Distribution"` comment column with joined
      labels (ARCtrl: no multi-output-column Measurement row)
- [x] 3.4 Add unit test: single DataDownload → Investigation + Measurement
      `"Distribution"` comments
- [x] 3.5 Add unit test: multiple DataDownload → joined Measurement cell
      (no extra output columns)

## 4. Documentation

- [x] 4.1 Create `docs/schemaorg_mapping.md` with field tables (Dataset → Investigation, Study, Assay)
- [x] 4.2 Document identifier cascade precedence rule
- [x] 4.3 Document `@context` allowlist and extension mechanism

## 5. Validation

- [x] 5.1 `uv run ruff format middleware/linked_data/`
- [x] 5.2 `uv run ruff check middleware/linked_data/`
- [x] 5.3 `uv run pytest middleware/linked_data/tests -v --tb=short`
