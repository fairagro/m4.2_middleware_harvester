## 1. Register markers

- [ ] 1.1 Add `system_local` and `system_external` to `[tool.pytest.ini_options] markers` in root `pyproject.toml`
      (same meanings as API)
- [ ] 1.2 Keep existing `asyncio` / `unit` / `integration` entries

## 2. Audit suites

- [ ] 2.1 Grep for tests that clearly need `system_local` or `system_external` today
- [ ] 2.2 Apply remaps only if needed; otherwise document zero remaps in the PR

## 3. Verify + ready signal

- [ ] 3.1 Smoke: `uv run pytest --markers` lists both new markers; collect with
      `-m "not system_external and not system_local"` succeeds under `--strict-markers`
- [ ] 3.2 `openspec validate --changes`
- [ ] 3.3 Pause for user commit/push; draft PR with `Fixes #222`
- [ ] 3.4 After merge (or with PR): comment on Devinfra #120 that harvester registered the markers
