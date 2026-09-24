## 1. Scaffold package

- [x] 1.1 Add workspace package `middleware/generic` (pyproject, src layout, `py.typed`) and wire it into the root
      workspace / Docker Bake metadata the same way as `payload`/`linked_data`; verify `uv sync --dev --all-packages`
      succeeds
- [x] 1.2 Update `openspec/principles.md` module graph for `generic/` → `payload/` and temporary `linked_data` →
      `generic.discovery`; verify the graph section mentions `generic` and forbids plugin↔plugin imports

## 2. Discovery types + abstractions

- [x] 2.1 Move `DiscoveryResult` hierarchy into `middleware.generic` (re-export from `linked_data` for compatibility);
      verify existing linked_data unit tests still pass
- [x] 2.2 Implement `Protocol` ABC + registry + `protocol_type` enum hooks; verify a unit test registers a fake protocol
      and resolves it by key
- [x] 2.3 Implement `PayloadParser` ABC + registry with `produces: PayloadKind` + `parser_type` enum hooks; verify a
      unit test registers a fake parser and asserts `produces`

## 3. Generic plugin + config

- [x] 3.1 Add `middleware.generic.config.Config` (`protocol_type`, `parser_type`, shared HTTP/sitemap fields as needed)
      and register `generic:` on `RepositoryConfig` with mutual exclusion + required `mapper:`; verify harvester config
      unit tests cover accept/reject cases
- [x] 3.2 Implement `GenericPlugin` orchestration (Protocol → Parser → kind-check → DataMapper → yield) reusing bounded
      pipeline approach; verify unit tests cover success, kind mismatch, and forwarded
      `SkippedRecord`/`RecordProcessingError`
- [x] 3.3 Implement `get_expected_datasets()` via Protocol with soft-`None` on failure; verify unit test covers success
      and failure-to-None

## 4. First migration (xml + html_jsonld)

- [x] 4.1 Port/move XML sitemap Protocol into `generic` and shim `linked_data` `SitemapType.xml` to the same
      implementation; verify xml sitemap unit/integration tests still pass via both entry points where applicable
- [x] 4.2 Port/move HtmlJsonLd PayloadParser into `generic` and shim `linked_data` `DatasetType.html_jsonld`; verify
      html_jsonld tests still pass
- [x] 4.3 Add or switch one example/demo repository YAML to `generic:` with `protocol_type: xml`,
      `parser_type: html_jsonld`, and existing `mapper:`; verify config loads and a focused harvest/integration test (or
      CST/demo dry path) succeeds

## 5. Specs hygiene + follow-ups

- [x] 5.1 Ensure OpenSpec delta coverage matches implemented behaviour; run
      `openspec validate --change generic-harvest-plugin` (or project-equivalent) and fix drift
- [x] 5.2 Remaining migration tasks tracked as GitHub sub-issues of #141 (not a repo markdown checklist): #293
      `mycore_solr`, #294 `regal_*`, #295 YAML/Helm migrate, #296 deprecate/remove `linked_data`; related #142 OAI-PMH —
      do **not** implement them in this PR unless explicitly expanded

## 6. Pause for user commit / draft PR

- [x] 6.1 After implementation, pause for the user to commit/push; then open draft PR with `Fixes #141` when tip is
      ahead of `main` — https://github.com/fairagro/m4.2_middleware_harvester/pull/301
