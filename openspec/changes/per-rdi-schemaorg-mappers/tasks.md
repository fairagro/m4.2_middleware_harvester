## 1. Dialect seams (no behaviour change)

- [x] 1.1 Convert `LinkedDataMapper._stable_wrap` from `@staticmethod` to an instance method; update `GeneralSchemaOrgMapper` and `RegalMapper` overrides
- [x] 1.2 Collapse `GeneralSchemaOrgMapper.SCHEMA_URIS` into the single `SCHEMA_ORG_NAMESPACES` source; drive Dataset `rdf:type` selection from the same tuple the wrap receives
- [x] 1.3 Run the full linked_data suite unchanged to prove the refactor is inert (Regal stability, Schema.org identifier, concurrent `map_graph` guards)

## 2. Overlay selection mechanism

- [x] 2.1 Add optional `mapper: str | None` to `middleware/linked_data/config.py` with a Pydantic `description` (no `PayloadType` change)
- [x] 2.2 Add `LinkedDataMapper.overlay_registry: Registry[str, LinkedDataMapper]` plus a `register_overlay(name)` classmethod
- [x] 2.3 Add `BUILDS_ON: ClassVar[PayloadType | None]` to `LinkedDataMapper`; overlays declare their base payload format
- [x] 2.4 Extend `LinkedDataPlugin.create_mapper`: resolve from `overlay_registry` when `config.mapper` is set, else from the `payload_type` registry; raise a configuration error naming the value on unknown mapper or `BUILDS_ON` / `payload_type` mismatch

## 3. Title fallback hook and OpenAgrar overlay

- [x] 3.1 Add frozen `ResolvedField(value, source)` dataclass
- [x] 3.2 Add `GeneralSchemaOrgMapper.TITLE_SOURCES = ("schema:name",)` and public `resolve_title_fallback(dataset: ResourceView, context: MappingContext) -> ResolvedField | None` returning null in the base
- [x] 3.3 Rewrite `_SchemaOrgRun._resolve_dataset_title` to try `schema:name`, delegate to the hook, then raise; error message lists `TITLE_SOURCES`
- [x] 3.4 Confirm `Title Source` comment + WARNING log stay in the shared mapper (`_add_title_fallback_comment` unchanged)
- [x] 3.5 Add `linked_data_mapper/openagrar_schema_org_mapper.py`: `OpenAgrarSchemaOrgMapper(GeneralSchemaOrgMapper)`, overlay name `openagrar`, `BUILDS_ON = PayloadType.schema_org_general`, `#164`'s chain in `resolve_title_fallback`, overridden `TITLE_SOURCES`
- [x] 3.6 Export the overlay from `linked_data_mapper/__init__.py` so registration happens on package import
- [x] 3.7 Verify no RDI-specific string (`edal`, `pgp`, `openagrar`, `mycore`) remains in `general_schema_org_mapper.py`

## 4. Configuration

- [x] 4.1 Add `mapper: openagrar` to the two OpenAgrar examples in `helm/harvester/values.yaml` with an explanatory comment
- [x] 4.2 Leave `dev_environment/*.yaml` `edal` untouched (no e!DAL overlay — design decision 5)

## 5. Tests

- [x] 5.1 Add `tests/unit/test_openagrar_mapper.py`: headline / first-non-empty alternativeHeadline / html_title fallbacks, `Title Source` comment, WARNING log, no-carrier fail-closed naming all four carriers
- [x] 5.2 Add overlay parity test: `schema:name` present → same identifier and title as `GeneralSchemaOrgMapper`, no `Title Source` comment
- [x] 5.3 Rework `tests/unit/test_mapper_title_fallback.py` to assert the shared mapper fails closed on each `#164` fixture and names only `schema:name`
- [x] 5.4 Keep `test_edal_pgp_sibling_replicates_get_distinct_identifiers_not_title_slug` on `GeneralSchemaOrgMapper`; note in its docstring that the cascade is RDI-agnostic and e!DAL has no overlay
- [x] 5.5 Add config/plugin tests: `mapper` unset → base mapper; `mapper: openagrar` → overlay; unknown mapper → error; `BUILDS_ON` mismatch → error
- [x] 5.6 Add concurrent `map_graph` cross-talk guard for the overlay (mirrors the shared-mapper guard)

## 6. Docs and follow-ups

- [ ] 6.1 Add an "RDI overrides" section to `docs/schemaorg_mapping.md` listing the OpenAgrar overlay and its title chain, cross-referencing `#170`
- [ ] 6.2 Add an RDI-onboarding template anchored to the OpenAgrar overlay as the worked example
- [ ] 6.3 File a follow-up issue: move the JSON-LD `@context` allowlist out of `jsonld_validation.py`'s module constant into a mapper-declared contribution (dialect blocker crossing into the dataset layer)
- [ ] 6.4 Record on `#227` that `#125` carried no e!DAL-specific code and no `EdalPgpSchemaOrgMapper` was created

## 7. Validation

- [ ] 7.1 `uv run ruff format middleware/linked_data/` and `uv run ruff check middleware/linked_data/`
- [ ] 7.2 `uv run mypy --config-file pyproject.toml` and `uv run pylint` on the affected package
- [ ] 7.3 `uv run pytest middleware/linked_data/tests/unit/ -v`
- [ ] 7.4 `openspec validate per-rdi-schemaorg-mappers --strict`
