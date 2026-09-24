## Why

Devinfra [#120](https://github.com/fairagro/m4.2_middleware_devinfra/issues/120) will change the synced pre-push pytest
entry to exclude expensive markers:

```bash
uv run pytest -m "not system_external and not system_local"
```

This repo already enables `--strict-markers` and only registers `unit` / `integration` / `asyncio`. Unknown markers in
the `-m` expression make the fleet-wide synced hook unsafe for harvester until the markers are registered (same wording
as the API product).

## What Changes

- Add `system_local` and `system_external` to `[tool.pytest.ini_options] markers` in root `pyproject.toml`, matching API
  meanings (local/testcontainers vs real external systems/secrets).
- Audit existing suites for markers that should use the new names; remapping may be **zero** for this MVP (existing
  `@pytest.mark.integration` CSW suites stay as-is unless clearly in scope).
- After merge: comment on Devinfra #120 that harvester has registered the markers (ready signal).

## Capabilities

### New Capabilities

- (none — `skip_specs: true`)

### Modified Capabilities

- (none — tooling / pytest config only; no harvester plugin behaviour change)

## Impact

- Pre-push after Devinfra #120 sync: `-m` expression parses cleanly under `--strict-markers`.
- CI / intentional local runs can still select `system_*` once tests use those markers.
- Non-goals: forking synced `.pre-commit-config.yaml`, changing CI reusable defaults, remapping all `integration` tests
  unless required for the ready signal.
