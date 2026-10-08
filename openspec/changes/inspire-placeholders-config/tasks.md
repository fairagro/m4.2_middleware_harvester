# Tasks

## 1. INSPIRE parser config

- [x] 1.1 Add `IsoParserConfig` (`value_bounds`, `placeholders`) to `middleware.inspire.config`; make `Config` extend
      it; verify `inspire.placeholders` loads and defaults to an empty `PlaceholderConfig`
- [x] 1.2 Add `validation_context(value_bounds, placeholders)` to `middleware.payload.inspire.models`; make the context
      keys private; verify a unit test validates a record through the returned context
- [x] 1.3 `IsoParser(config: IsoParserConfig)` and `CSWClient(config)`; drop the placeholders argument; update tests
- [x] 1.4 `InspirePlugin` stops reading `mapper_config.placeholders`; verify a plugin test that `inspire.placeholders`
      reaches the parser

## 2. Deprecated mapper.placeholders on inspire

- [x] 2.1 `RepositoryConfig` validator lifts an explicitly set `mapper.placeholders` to `inspire.placeholders` with a
      `logger.warning`; error when both are set and differ; verify with `caplog` unit tests (lift, conflict, no warning
      when unset, linked-data repos untouched)
- [x] 2.2 Move in-repo INSPIRE examples (`helm/harvester/values.yaml`, `dev_environment`) to `inspire.placeholders`
- [x] 2.3 Open a follow-up issue (#477) to reject `mapper.placeholders` on `inspire`, with the m4.2_infrastructure
      migration as prerequisite

## 3. LinkedDataMapper placeholders

- [x] 3.1 `LinkedDataMapper.__init__(placeholders)`, `placeholders` property and `license()` helper; base `from_config`
      passes `config.placeholders`
- [x] 3.2 `GeneralSchemaOrgMapper`, `RegalMapper`, `CkanextDcatMapper` use the base; verify existing mapper tests pass

## 4. Docs and specs

- [x] 4.1 Placeholder contract section in `docs/mappers/{inspire,schemaorg,regal}.md`; README pointer
- [x] 4.2 Validate: `openspec validate inspire-placeholders-config`, `uv run ruff format`, ruff, mypy, pylint, and
      `uv run pytest` for `middleware/inspire`, `middleware/payload`, `middleware/harvester`
