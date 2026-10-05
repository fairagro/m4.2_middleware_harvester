## 1. Implementation

- [x] 1.1 `MapperConfig.placeholder_values`; remove `ValueBounds.placeholder_values`
- [x] 1.2 INSPIRE: plugin → `CSWClient` → `IsoParser` → validation context
- [x] 1.3 Schema.org and Regal mappers and `license_from_value` take the list
- [x] 1.4 Unit tests; docs (`inspire_mapping.md`, `schemaorg_mapping.md`, `config.all-rdis.yaml` example)

## 2. Validation

- [x] 2.1 ruff, mypy, pylint, bandit
- [x] 2.2 `uv run pytest middleware/`
- [x] 2.3 Live BonaRes with defaults unchanged (274 valid)
