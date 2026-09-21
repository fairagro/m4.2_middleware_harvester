## 1. Scaffold package

- [ ] 1.1 Add workspace package `middleware/generic` (pyproject, src layout, `py.typed`) and wire it into the root workspace / Docker Bake metadata the same way as `payload`/`linked_data`; verify `uv sync --dev --all-packages` succeeds
- [ ] 1.2 Update `openspec/principles.md` module graph for `generic/` → `payload/` and temporary `linked_data` → `generic.discovery`; verify the graph section mentions `generic` and forbids plugin↔plugin imports

## 2. Discovery types + abstractions

- [ ] 2.1 Move `DiscoveryResult` hierarchy into `middleware.generic` (re-export from `linked_data` for compatibility); verify existing linked_data unit tests still pass
- [ ] 2.2 Implement `Protocol` ABC + registry + `protocol_type` enum hooks; verify a unit test registers a fake protocol and resolves it by key
- [ ] 2.3 Implement `PayloadParser` ABC + registry with `produces: PayloadKind` + `parser_type` enum hooks; verify a unit test registers a fake parser and asserts `produces`

## 3. Generic plugin + config

- [ ] 3.1 Add `middleware.generic.config.Config` (`protocol_type`, `parser_type`, shared HTTP/sitemap fields as needed) and register `generic:` on `RepositoryConfig` with mutual exclusion + required `mapper:`; verify harvester config unit tests cover accept/reject cases
- [ ] 3.2 Implement `GenericPlugin` orchestration (Protocol → Parser → kind-check → DataMapper → yield) reusing bounded pipeline approach; verify unit tests cover success, kind mismatch, and forwarded `SkippedRecord`/`RecordProcessingError`
- [ ] 3.3 Implement `get_expected_datasets()` via Protocol with soft-`None` on failure; verify unit test covers success and failure-to-None

## 4. First migration (xml + html_jsonld)

- [ ] 4.1 Port/move XML sitemap Protocol into `generic` and shim `linked_data` `SitemapType.xml` to the same implementation; verify xml sitemap unit/integration tests still pass via both entry points where applicable
- [ ] 4.2 Port/move HtmlJsonLd PayloadParser into `generic` and shim `linked_data` `DatasetType.html_jsonld`; verify html_jsonld tests still pass
- [ ] 4.3 Add or switch one example/demo repository YAML to `generic:` with `protocol_type: xml`, `parser_type: html_jsonld`, and existing `mapper:`; verify config loads and a focused harvest/integration test (or CST/demo dry path) succeeds

## 5. Specs hygiene + follow-ups

- [ ] 5.1 Ensure OpenSpec delta coverage matches implemented behaviour; run `openspec validate --change generic-harvest-plugin` (or project-equivalent) and fix drift
- [ ] 5.2 Document remaining migration tasks (`mycore_solr`, `regal_find`/`regal_jsonld`, deprecate `linked_data`) as unchecked follow-ups or linked issues — verify the doc/issue list exists; do **not** implement them in this PR unless explicitly expanded

## 6. Pause for user commit / draft PR

- [ ] 6.1 After implementation, pause for the user to commit/push; then open draft PR with `Fixes #141` when tip is ahead of `main`
