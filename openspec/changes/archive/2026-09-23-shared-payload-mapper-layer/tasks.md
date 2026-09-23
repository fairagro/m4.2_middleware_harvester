## 1. Package scaffold

- [x] 1.1 Add uv workspace member `middleware/payload` (`pyproject.toml`, `src/middleware/payload/`)
- [x] 1.2 Wire workspace dependency: `linked_data` and `harvester` depend on `middleware.payload`; `uv sync`
- [x] 1.3 Extend MYPYPATH / quality path overlays if needed for the new package

## 2. Core payload contracts

- [x] 2.1 Implement `PayloadKind` (`rdf_graph` only), `ParsedPayload`, and `DataMapper` ABC + registry with `accepts`
- [x] 2.2 Unit tests for registry resolution and kind `accepts`

## 3. Move RDF mapping stack (behaviour-preserving)

- [x] 3.1 Move `stable_graph`, `LinkedDataMapper`, Schema.org + Regal mappers, and package `__init__` into
      `middleware.payload`; keep call-scoped StableGraph / `_*Run` contracts
- [x] 3.2 Update production and test imports; remove empty `linked_data/linked_data_mapper` (or thin re-export only if
      unavoidable — prefer zero re-exports)
- [x] 3.3 Existing mapper unit tests pass from new package paths

## 4. Repository mapper config

- [x] 4.1 Add `mapper` model (`type`, optional mapper-specific fields as needed) to `RepositoryConfig`; exclude
      `mapper` from exactly-one-plugin field set
- [x] 4.2 Require `mapper` for `linked_data` repositories; validate registered type and `accepts == rdf_graph`
- [x] 4.3 Keep `payload_type` on linked_data plugin `Config` as `Field(deprecated=True)`; lift to
      `mapper.type` with `logger.warning` (conflict fails closed)
- [x] 4.4 Unit tests: valid linked_data+mapper; missing mapper; unknown type; inspire without mapper still OK;
      legacy `payload_type` lift / conflict
- [x] 4.5 Update example/demo YAML and fixtures to `mapper.type`

## 5. linked_data wiring

- [x] 5.1 `LinkedDataPlugin` resolves mapper from shared registry via repository `mapper` config
- [x] 5.2 Pass discovery URL / harvest_source_id via `MappingContext`; harvest behaviour parity
- [x] 5.3 Update linked_data plugin/integration tests for new config shape

## 6. Validation

- [x] 6.1 `uv run ruff format` / `ruff check` on affected packages
- [x] 6.2 `uv run pytest` for `middleware/payload`, `middleware/linked_data`, harvester config tests
- [x] 6.3 `openspec validate --change shared-payload-mapper-layer`
- [x] 6.4 Pause for user commit/push; draft PR with `Fixes #140`
