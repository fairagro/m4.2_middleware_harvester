## 1. Title fallback cascade (mapper)

- [x] 1.1 `_resolve_dataset_title`: `schema:name` → `schema:headline` → first
      non-empty `schema:alternativeHeadline` (document order) → HTML title
      hint; fail closed with no usable title
- [x] 1.2 Record fallback source as `"Title Source"` Investigation Comment
      and WARNING log; never log a raw rdflib blank-node subject

## 2. HTML title hint (dataset / plugin)

- [x] 2.1 `Dataset.title_hint()` / `HtmlJsonLdDataset.title_hint()`:
      `citation_title` meta, else `<title>` text
- [x] 2.2 `Dataset.title_hint_from_cache()` / `HtmlJsonLdDataset` override:
      same, but no I/O — uses HTML already fetched by `to_graph()`
- [x] 2.3 `MappingContext.html_title` is a lazy zero-arg callable; plugin
      passes `dataset.title_hint_from_cache` (not an eagerly awaited value)

## 3. Unit tests

- [x] 3.1 `schema:name` present: no fallback, no Comment, no warning
- [x] 3.2 `headline` fallback: Comment + WARNING; no blank-node label logged
- [x] 3.3 `alternativeHeadline` fallback picks first entry in document
      order, not alphabetical order
- [x] 3.4 HTML title hint fallback via `MappingContext.html_title`
- [x] 3.5 HTML title provider is not called when `schema:name` is present
- [x] 3.6 No usable title anywhere: fails closed, no `"Untitled"`
- [x] 3.7 `title_hint()` / `_ensure_jsonld_blocks()` reuse fetched HTML in
      both call orders (only one HTTP fetch either way)

## 4. Documentation

- [x] 4.1 This proposal's spec delta merged into
      `openspec/specs/schemaorg-to-arc-mapping/spec.md`

## 5. Validation

- [x] 5.1 `uv run ruff format --check --config ruff.toml middleware/linked_data`
      / `uv run ruff check --config ruff.toml middleware/linked_data`
- [x] 5.2 `uv run pylint middleware/linked_data/src/ middleware/linked_data/tests/unit/`
- [x] 5.3 `uv run pytest middleware/linked_data/tests/unit -q`
