# Tasks

## 1. Package scaffold

- [x] 1.1 Create `middleware/parsing` workspace package (pyproject with deps on `payload` + harvester/shared as needed,
      src layout, tests dir) and register it in the root uv workspace; verify `uv sync --dev --all-packages` and
      `import middleware.parsing` succeed
- [x] 1.2 Wire MYPYPATH / PYLINT_SOURCE_ROOTS / root `pyproject.toml` path lists / AGENTS quality mentions for
      `middleware/parsing`; verify path overlays include `middleware/parsing/src`
- [x] 1.3 Extend `.importlinter`: add `middleware.parsing` to root packages; forbid `payload → parsing`; forbid
      `parsing →` protocol plugins; allow `parsing → harvester` (do not list harvester under parsing isolation
      forbidden); verify `lint-imports` (or project import-linter command) passes on the updated contracts

## 2. Move shared types and parsers

- [x] 2.1 Move `DiscoveryResult` / `UrlDiscoveryResult` / `JsonLdDiscoveryResult` into `middleware.parsing`; verify unit
      tests import from the new module
- [x] 2.2 Move `ParserType`, `PayloadParser` ABC + registry, and `html_jsonld` parser into `middleware.parsing`; keep
      `NiceHttpClient` annotations and `HarvesterError`-based parser errors; verify registry tests and html_jsonld unit
      tests pass from the new package
- [x] 2.3 Add `register_builtin_parsers` (or equivalent) side-effect import gate in `parsing`; verify builtins register
      on import

## 3. Update consumers

- [x] 3.1 Update `middleware.generic` to import discovery/parsers from `parsing`; remove moved modules (no permanent
      re-exports unless a short deprecation is explicitly required); verify `middleware/generic` unit tests pass
- [x] 3.2 Update `middleware.linked_data` discovery/parser imports to `parsing` (keep any remaining Protocol/generic
      shims only where still needed); verify `middleware/linked_data` unit tests pass
- [x] 3.3 Update `middleware.harvester` config validation to resolve `PayloadParser` from `parsing`; verify harvester
      config unit tests pass

## 4. Docs and OpenSpec narrative

- [x] 4.1 Update `openspec/principles.md` module graph for `parsing` (deps and non-deps); verify the narrative matches
      the `principles` / `shared-parsing` delta specs
- [x] 4.2 Run `openspec validate --changes` (or change-scoped validate) for `shared-parsing-package`; verify the change
      validates
- [x] 4.3 Format OpenSpec change Markdown with Prettier (`npx prettier --write openspec/changes/shared-parsing-package`)
      and verify `npx prettier --check` on that tree is clean

## 5. Integration check

- [x] 5.1 Run targeted pytest for `middleware/parsing`, `middleware/generic`, `middleware/linked_data`, and affected
      harvester config tests; verify green
- [x] 5.2 Confirm non-goals: no OAI package, no new RDF/XML parser, no EPrints mapper in this PR
- [x] 5.3 Lift shared parser selection to repository sibling `parser: { type }` (like `mapper:`), remove
      `generic.parser_type` (hard cut), update GenericPlugin/orchestrator/examples/tests; verify config unit tests for
      require-parser and happy path
