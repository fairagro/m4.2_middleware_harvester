## 1. Implementation

- [x] 1.1 `arc_license` helper module with unit tests
- [x] 1.2 Schema.org, Regal and INSPIRE mappers set `ARC.License`
- [x] 1.3 Round-trip test: RO-Crate → `ARC.from_rocrate_json_string` → `Write` gives a `LICENSE` file, no URL paths
- [x] 1.4 Docs: `schemaorg_mapping.md`, `regal_mapping.md`, `inspire_mapping.md`

## 2. Validation

- [x] 2.1 ruff, mypy, pylint, prettier
- [x] 2.2 `uv run pytest middleware/`
- [x] 2.3 Live/dump classification per RDI (see proposal Impact)
