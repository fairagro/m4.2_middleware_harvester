## 1. Implementation

- [x] 1.1 `PlaceholderConfig` (`values`, `unrendered_templates`, empty defaults) as `MapperConfig.placeholders`; remove
      `ValueBounds.placeholder_values` and the built-in default list
- [x] 1.2 INSPIRE: plugin → `CSWClient` → `IsoParser` → validation context; no defaults outside the model
- [x] 1.3 Schema.org and Regal mappers and `license_from_value` take the `PlaceholderConfig`
- [x] 1.4 Unit tests; docs (`inspire_mapping.md`, `schemaorg_mapping.md`), `config.all-rdis.yaml`, Helm example

## 2. Validation

- [x] 2.1 ruff, mypy, pylint, bandit
- [x] 2.2 `uv run pytest middleware/`
- [x] 2.3 Live BonaRes (`repository.zalf.de`, 2026-10-06): without `mapper.placeholders` 269 ARCs, placeholders kept;
      with `values: ["None", "No information provided"]` 285 ARCs, none of the two values left (only placeholder
      abstracts, #431)
