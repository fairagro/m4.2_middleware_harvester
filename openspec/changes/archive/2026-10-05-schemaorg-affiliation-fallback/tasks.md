## 1. Implementation

- [x] 1.1 Affiliation fallback from a flat address; comma-only addresses are absent
- [x] 1.2 PostalAddress keeps `addressLocality` and `addressRegion`
- [x] 1.3 Unit tests
- [x] 1.4 Docs: `schemaorg_mapping.md`

## 2. Validation

- [x] 2.1 ruff, mypy, pylint, bandit
- [x] 2.2 `uv run pytest middleware/`
- [x] 2.3 Live e!DAL (338 records, before/after diff)
