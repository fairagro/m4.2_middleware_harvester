## 1. Implementation

- [x] 1.1 `doi_ids_as_iris` in `middleware.parsing`, used by the `html_jsonld` and `jsonld` parsers
- [x] 1.2 Unit tests, including e!DAL HTML → ARC with a typed DOI
- [x] 1.3 Docs: `schemaorg_mapping.md`

## 2. Validation

- [x] 2.1 ruff, mypy, pylint, bandit; `uv run pytest middleware/`
- [x] 2.2 Live e!DAL (338)
