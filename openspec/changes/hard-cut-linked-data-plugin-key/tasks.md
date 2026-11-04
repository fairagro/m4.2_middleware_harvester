# Tasks

## 1. Harvester: drop plugin key

- [ ] 1.1 Remove `linked_data` from `RepositoryConfig` (field, imports, `payload_type` lift, deprecation warning,
      mapper/resource validators) so leftover YAML fails closed with a migration-oriented error; verify with unit tests
      that `linked_data:` rejects and `generic:` still loads —
      `uv run pytest middleware/harvester/tests/unit/test_config.py -q`
- [ ] 1.2 Remove `LinkedDataPlugin` from `PLUGIN_FACTORIES` / orchestrator branches; verify no `middleware.linked_data`
      imports remain under `middleware/harvester` (`rg middleware.linked_data middleware/harvester`)

## 2. Remove linked_data package

- [ ] 2.1 Delete `middleware/linked_data` (sources + tests) and drop workspace / harvester dependency / `pyproject.toml`
      / quality path / MYPYPATH / PYLINT / import-linter / Docker references; verify `uv sync --dev --all-packages` and
      `rg "middleware\\.linked_data|middleware/linked_data" --glob '!openspec/changes/archive/**'` shows only
      intentional docs/history (or none outside this change)

## 3. Docs and examples

- [ ] 3.1 Rewrite `docs/linked_data_to_generic.md` from “deprecated shim” to “plugin key removed”; scrub Helm /
      `dev_environment` comments that still advertise `linked_data:` as supported; verify
      `rg "linked_data: plugin key is deprecated|temporary shim" docs helm`
- [ ] 3.2 Update `openspec/principles.md` and `AGENTS.md` module graphs / package lists to drop `linked_data` plugin
      package; verify they list `inspire` / `generic` / `oai_pmh` only as protocol plugins

## 4. Spec / quality gate

- [ ] 4.1 Confirm delta specs match implemented rejection + package removal; run
      `openspec validate --change hard-cut-linked-data-plugin-key` (or project equivalent) and focused pytest
      (`middleware/harvester`, `middleware/generic` skipped-datasets / discovery dedupe) — verify green
