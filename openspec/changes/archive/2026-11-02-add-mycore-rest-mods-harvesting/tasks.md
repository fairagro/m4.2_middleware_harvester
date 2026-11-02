## 1. Shared discovery and payload types

- [ ] 1.1 Add optional `fetch_url` to `UrlDiscoveryResult` (`middleware.parsing.discovery`); verify existing
      parsing/generic tests still pass unchanged
- [ ] 1.2 Make `HtmlJsonLdParser` fetch `fetch_url or url`; verify with a unit test that a unit with `fetch_url`
      requests only that URL and reports errors under `identifier`
- [ ] 1.3 Add `PayloadKind.mods_record`, `ParserType.mods_xml`, `MapperType.mods_general` (empty `extra="forbid"` type
      config); verify config tests for `mapper: { mods_general: {} }` and an unknown field
- [ ] 1.4 Add a small shared safe-XML helper in `middleware.parsing` (defusedxml) if both protocol and parser need it;
      verify an internal/external-entity fixture fails closed

## 2. mycore_rest Protocol

- [ ] 2.1 Implement `MycoreRestProtocolConfig` (`entry_url`, `page_size` default 1000) and `MycoreRestProtocol`
      registered as `ProtocolType.mycore_rest`; verify registry/config validation tests
- [ ] 2.2 Implement list paging (`limit`, `after_id`, software-owned paging params, stop on short or empty page); verify
      with mocked-HTTP tests for 1 page, 2 pages, and operator `offset`/`after_id` ignored
- [ ] 2.3 Yield `UrlDiscoveryResult` with landing `/receive/{id}`, `harvest_source_id`, and `fetch_url`, including a
      context path prefix; verify the OpenAgrar example and that identity equals `mycore_solr` for the same id
- [ ] 2.4 Implement `get_expected_count` from `X-Total-Count` with first-page reuse; verify the count, the missing
      header, and that only one list request is issued
- [ ] 2.5 Error handling: wrong root or malformed XML raises `GenericProtocolError`, a missing id yields
      `RecordProcessingError`, HTTP errors propagate; verify with unit tests

## 3. mods_xml parser and mods_record model

- [ ] 3.1 Add the `ModsRecord` Pydantic models in `middleware/payload/mods/models.py` (titles, abstracts, names,
      identifiers, dates, access conditions, classifications, genres, subjects, languages, urls, object id); verify
      model unit tests
- [ ] 3.2 Implement `ModsXmlParser` (URL unit via `fetch_url or url`, inline `XmlDiscoveryResult`, MyCoRe envelope or
      bare `mods:mods`); verify with tests using a trimmed real OpenAgrar fixture (`openagrar_mods_00087541`) and a
      bare-MODS fixture
- [ ] 3.3 Fail-closed cases (empty body, malformed XML, wrong root, zero or several `mods:mods`, entity fixture); verify
      each raises `ParserError`

## 4. mods_general mapper and docs

- [ ] 4.1 Write `docs/mappers/mods.md` (base sections, `payload_kind: mods_record`, `mapper_id: mods_general`) and list
      it in `docs/mappers/README.md`; verify against the mapper-docs requirements
- [ ] 4.2 Implement `ModsMapper` (identity cascade, title refusal, Persons with ORCID/affiliation, no Persons for
      corporate names, DOI/licence/dates/subjects via shared helpers); verify with mapper unit tests per
      `mods-to-arc-mapping` scenario
- [ ] 4.3 Register the mapper in `register_builtin_mappers`; verify that a generic config with `parser.mods_xml` +
      `mapper.mods_general` passes kind alignment

## 5. Integration and verification

- [ ] 5.1 Add a generic-plugin test with mocked HTTP (list + 2 objects) through `mycore_rest` → `mods_xml` →
      `mods_general`; verify 2 `HarvestedArc` values with landing source URLs and MyCoRe-id identifiers
- [ ] 5.2 Add an example `openagrar` repository block (REST config, `worker_tasks: 1`) to the config example/docs;
      verify it loads with `Config.from_yaml_file`
- [ ] 5.3 Run one live OpenAgrar comparison (container and source, sequential, small limit) between `schema_org_general`
      and `mods_general`; record the ARC payload diff (identifiers equal, DOI and licence added) in the PR
- [ ] 5.4 Update the AGENTS.md spec index with the three new domains; verify the links resolve
- [ ] 5.5 Run `uv run ruff format middleware/`, ruff check, mypy (CI-equivalent), pylint, and
      `uv run pytest middleware/generic middleware/parsing middleware/payload`; then
      `openspec validate add-mycore-rest-mods-harvesting`
