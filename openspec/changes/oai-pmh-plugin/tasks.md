# Tasks

## 1. Prerequisites and package scaffold

- [ ] 1.1 Confirm #339 (`middleware.parsing`, sibling `parser:`, `ParserConfig`) is on the integration base; if missing,
      stop and land #339 first — verify by importing `middleware.parsing.parser.parser.PayloadParser` and
      `middleware.parsing.parser_config.ParserConfig`
- [ ] 1.2 Add workspace package `middleware/oai_pmh` (pyproject, src layout, tests dir) and wire it into the root uv
      workspace / quality path overlays; verify `uv sync --dev --all-packages` succeeds and the package is importable as
      `middleware.oai_pmh`
- [ ] 1.3 Add dependency `oaipmh-scythe` to the OAI package only; verify the package resolves and `import oaipmh_scythe`
      works in the project env

## 2. Shared RDF/XML parser and discovery unit

- [ ] 2.1 Add a `middleware.parsing` inline discovery subclass carrying a stable `identifier` plus RDF/XML text/bytes
      (beside `UrlDiscoveryResult` / `JsonLdDiscoveryResult`); verify unit construction
- [ ] 2.2 Implement shared inline RDF/XML `PayloadParser` (`ParserType.rdf_xml` / `parser.type: rdf_xml`) that builds
      `ParsedPayload(kind=rdf_graph)` from that discovery unit without requiring HTTP; raise `ParserError` on missing or
      malformed RDF/XML; verify unit tests for happy path, missing metadata, and malformed RDF/XML
- [ ] 2.3 Register the parser in `register_builtin_parsers` (or equivalent import gate); verify registry lookup by
      `rdf_xml` and `produces == rdf_graph`
- [ ] 2.4 Add OpenSpec-facing fixture XML (minimal OAI `<metadata>` RDF/XML sample) under parsing or OAI tests; verify
      tests load the fixture without network

## 3. OAI plugin config and Scythe wiring

- [ ] 3.1 Implement `oai_pmh` Pydantic `Config` with `endpoint_url`, `metadata_prefix`, `sets: list[str]`, own
      HTTP/retry fields, optional `respect_robots_txt` / `max_requests_per_second` — **no** `parser_type` field; verify
      validation unit tests (required prefix, default empty sets, rejection of invalid types)
- [ ] 3.2 Implement helper that builds Scythe `HTTPConfig` / `RetryConfig` from plugin config (user agent, timeout,
      retries) and constructs a `Scythe` client; verify unit test that user agent and timeout are applied to the
      constructed configs
- [ ] 3.3 Implement robots preflight and optional per-host rate limiting around Scythe calls; verify unit tests for
      disallow → fail/skip closed and that rate-limit sleep is invoked when configured

## 4. Harvest loop

- [ ] 4.1 Implement ListRecords iteration with resumption (via Scythe), mapping each non-deleted record to the parsing
      inline discovery unit (OAI identifier + metadata XML); verify unit tests with mocked/paged Scythe responses
- [ ] 4.2 Implement empty-`sets` vs multi-`sets` sequential passes; verify tests cover unfiltered harvest and two-set
      sequential calls
- [ ] 4.3 Yield `SkippedRecord` for `header` deleted status without calling parser/mapper; verify skipped-datasets unit
      test
- [ ] 4.4 Implement `OaiPmhPlugin` constructed with `(config, mapper_config, parser_config)`: resolve parser from
      `middleware.parsing`, parse → kind check → shared `DataMapper` → `HarvestedArc` / record-level errors; catch
      `ParserError` as record-scoped; verify plugin unit tests for success, kind mismatch, and parse failure
      continuation
- [ ] 4.5 Implement `get_expected_datasets()` returning `None` unless a cheap reliable size is available; verify default
      `None` test

## 5. Orchestrator and configuration integration

- [ ] 5.1 Register `oai_pmh` on `RepositoryConfig` and require sibling `mapper` + `parser` with parser/mapper kind
      alignment at startup (mirror `validate_mapper_and_parser_for_generic`); verify harvester config unit tests (accept
      alone with `parser`+`mapper`, reject with second plugin, missing mapper, missing parser, kind mismatch)
- [ ] 5.2 Register plugin in orchestrator `PLUGIN_FACTORIES` and pass `(plugin_config, mapper, parser)` like `generic`;
      verify dispatch test or import smoke that resolves `oai_pmh`
- [ ] 5.3 Update `.importlinter` and `openspec/principles.md` module graph for `middleware.oai_pmh` (may import
      harvester + payload + parsing; must not import other plugins; payload must not import oai); verify import-linter
      contract run passes
- [ ] 5.4 Update AGENTS.md / quality path lists / `product.env` overlays if needed for the new package; verify
      documented commands still refer to real paths

## 6. Integration check

- [ ] 6.1 Run targeted pytest for `middleware/oai_pmh` and shared RDF/XML parser tests plus affected harvester config
      tests; verify green
- [ ] 6.2 Run `openspec validate --changes` (or change-scoped validate) for `oai-pmh-plugin`; verify the change
      validates
- [ ] 6.3 Confirm non-goals still hold: no EPrints mapper package, no aeprints production config required for merge;
      note follow-ups (API delete issue still separate)
