## 1. Package scaffold

- [ ] 1.1 Add uv workspace member `middleware/payload` (`pyproject.toml`, package layout under `src/middleware/payload/`)
- [ ] 1.2 Wire workspace dependency: `linked_data` and `harvester` depend on `middleware.payload`; run `uv sync`

## 2. Core payload contracts

- [ ] 2.1 Implement `PayloadKind` (`rdf_graph` only in v1), `ParsedPayload`, and `DataMapper` ABC + registry with `accepts: PayloadKind`
- [ ] 2.2 Move `LinkedDataMapper`, Schema.org mapper, Regal mapper, and shared helpers (`stable_graph`, person helpers as needed) into `middleware.payload`; update imports
- [ ] 2.3 Add unit tests for registry resolution and kind `accepts` on registered RDF mappers

## 3. Repository mapper config

- [ ] 3.1 Add `mapper` model (at least `type`) to `RepositoryConfig` beside plugin keys; exclude `mapper` from exactly-one-plugin field set
- [ ] 3.2 Validate mapper type is registered and `accepts` matches linked_data producer kind (`rdf_graph`); fail fast on mismatch/unknown type
- [ ] 3.3 Unit tests for valid/invalid repository configs (missing mapper, bad type, kind mismatch)
- [ ] 3.4 Update example/demo YAML configs to use repository `mapper.type` (transitional `payload_type` alias only if needed for compatibility)

## 4. linked_data wiring

- [ ] 4.1 Change `LinkedDataPlugin` to resolve mapper from shared registry using repository `mapper` config
- [ ] 4.2 Ensure mapping path still passes discovery URL / harvest_source_id context; behaviour parity with existing harvest tests
- [ ] 4.3 Update linked_data unit/integration tests for new imports and config shape

## 5. Specs / principles text (implementation-facing)

- [ ] 5.1 Update `openspec/specs/principles/` dependency graph / extension points notes in design Key Decisions if maintained alongside code (full archive merge later)
- [ ] 5.2 Add brief `openspec/specs/payload/design.md` Key Decisions stub pointing at this change design (optional if archive will create it)

## 6. Validation

- [ ] 6.1 `uv run ruff format middleware/` and `uv run ruff check` on affected packages
- [ ] 6.2 `uv run pytest` for `middleware/payload`, `middleware/linked_data`, and harvester config tests
- [ ] 6.3 `openspec validate --change shared-payload-mapper-layer` (and `--strict` if used in CI)
