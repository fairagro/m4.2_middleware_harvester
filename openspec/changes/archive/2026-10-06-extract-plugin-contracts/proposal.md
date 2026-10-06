# Proposal

## Why

Protocol plugins and `middleware.parsing` import `HarvesterError`, `SkippedRecord`, `NiceHttpClient`, and `Plugin` from
`middleware.harvester` while most plugin `pyproject.toml` files do not declare `harvester`. Declaring `harvester` would
cycle with the orchestrator’s hard dependency on plugin packages. GitHub
[#155](https://github.com/fairagro/m4.2_middleware_harvester/issues/155) (Phase B; #108 closed as duplicate). `payload`
already owns `HarvestedArc` and person helpers; the remaining contract types still sit in the orchestrator package.

## What Changes

- Add a leaf uv workspace package `middleware/contracts` (`middleware.contracts`) that owns:
  - `HarvesterError`, `RecordProcessingError`, `SkippedRecord`
  - `NiceHttpClient` / `NiceHttpClientConfig` / robots helpers
  - the `Plugin` protocol
- Plugins, `parsing`, and `harvester` depend on `contracts`. Plugins and `parsing` MUST NOT import
  `middleware.harvester`. `contracts` MUST NOT import `harvester`, `parsing`, or protocol plugins. `contracts` MAY
  import `payload` only for `HarvestedArc` on the `Plugin` yield union.
- Leave orchestrator-only helpers (`format_exception_for_report`, harvest-id recovery) in `harvester`.
- Update `openspec/principles.md` and the listed spec domains so import paths and the module graph match.
- **BREAKING** (in-repo): import paths move; no long-lived `harvester` re-exports for plugins.

### Non-goals

- Isolated-install CI / standalone plugin wheels →
  [#450](https://github.com/fairagro/m4.2_middleware_harvester/issues/450)
- Moving `HarvestedArc` or person helpers (already in `payload`)
- Entry-point plugin discovery / dropping `harvester` → plugin package deps
- Hosting contracts in `fairagro-middleware-shared`
- Changing yield semantics, HTTP politeness, or skip counting

## Capabilities

### New Capabilities

- None. Ownership is an import-path / package-graph change on existing capabilities.

### Modified Capabilities

- `principles`: leaf `middleware.contracts` package; plugins/`parsing` MUST NOT import `harvester`.
- `error-handling`: `HarvesterError` / `RecordProcessingError` live in `middleware.contracts.errors`.
- `skipped-datasets`: `SkippedRecord` lives in `middleware.contracts.errors`.
- `shared-parsing`: `parsing` depends on `contracts` (and `payload`), not `harvester`.
- `nice-http-client`: `NiceHttpClient` lives in `middleware.contracts.nice_http_client`.

## Impact

- New workspace member `middleware/contracts`; MYPYPATH / pylint / quality overlays.
- Import rewrites across `inspire`, `linked_data`, `generic`, `oai_pmh`, `parsing`, `harvester`.
- Remove `harvester` from `oai_pmh` and `parsing` `pyproject.toml` (today those edges are circular).
- Tests follow the new import paths; harvest behaviour unchanged.
- Follow-up: [#450](https://github.com/fairagro/m4.2_middleware_harvester/issues/450).
