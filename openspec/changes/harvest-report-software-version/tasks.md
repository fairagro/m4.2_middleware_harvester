# Tasks

## 1. Dependency

- [ ] 1.1 Bump `fairagro-middleware-shared` to `>=14.2.0` (workspace consumers) and refresh `uv.lock`; verify
      `uv run python -c 'from middleware.shared.report import HarvestReport; HarvestReport(software_version="0")'` works

## 2. Wire version onto the report

- [ ] 2.1 Set `software_version=version("harvester")` when constructing `HarvestReport` in `run_orchestrator`; verify a
      unit test asserts the report field matches `importlib.metadata.version("harvester")`
- [ ] 2.2 Keep existing start log / `--version` behaviour; verify `test_main` version-flag tests still pass

## 3. Gate

- [ ] 3.1 Run `openspec validate harvest-report-software-version` and focused harvester pytest; verify green
