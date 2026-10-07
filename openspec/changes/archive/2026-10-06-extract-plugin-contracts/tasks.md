# Tasks

## 1. Scaffold `middleware.contracts`

- [x] 1.1 Add `middleware/contracts` uv package (`pyproject.toml`, hatch `src/middleware`, deps: pydantic, httpx,
      payload) and register it in root `pyproject.toml` workspace members / mypy paths; verify `uv sync --all-packages`
      lists `contracts`
- [x] 1.2 Add `contracts` to `.devcontainer/product.env` `MYPYPATH` (and pylint roots if tests land there) and to
      quality/pylint invocation lists that enumerate packages (`AGENTS.md` / quality scripts as needed); verify the env
      file contains `middleware/contracts/src`

## 2. Move plugin-facing errors

- [x] 2.1 Move `HarvesterError`, `RecordProcessingError`, and `SkippedRecord` to `middleware.contracts.errors`; keep
      `format_exception_for_report` / harvest-id helpers in `harvester`; verify `harvester` tests for report formatting
      still import from `middleware.harvester.errors`
- [x] 2.2 Add or move unit tests that construct `SkippedRecord` / `RecordProcessingError` from
      `middleware.contracts.errors` and verify they are not `HarvesterError` subclasses / exceptions as in
      skipped-datasets

## 3. Move NiceHttpClient and Plugin protocol

- [x] 3.1 Move `nice_http_client.py` (including robots helpers / `RobotsTxtDisallowedError`) to
      `middleware.contracts.nice_http_client` and relocate `middleware/harvester/tests/unit/test_nice_http_client.py`
      under `contracts`; verify `uv run pytest middleware/contracts/tests/unit/test_nice_http_client.py -q` passes
- [x] 3.2 Move the `Plugin` protocol to `middleware.contracts.plugin_base` (import `HarvestedArc` from `payload`);
      delete plugin-facing `middleware.harvester.plugin_base`; verify no `middleware.harvester.plugin_base` module
      remains

## 4. Honest package graph and imports

- [x] 4.1 Rewrite plugin, parsing, and harvester imports to `middleware.contracts`; add `contracts` to those packages’
      `pyproject.toml`; remove `harvester` from `parsing` and `oai_pmh` dependencies; verify
      `rg "from middleware\\.harvester" middleware/{inspire,linked_data,generic,oai_pmh,parsing}` is empty (tests
      included)
- [x] 4.2 Point harvester at `contracts` for types while keeping report helpers local; verify `middleware.harvester`
      modules do not re-export plugin-facing types for plugins to import
- [x] 4.3 Drop duplicate `linked_data` NiceHttpClient tests that only re-import the moved module, or retarget them;
      verify `uv run pytest middleware/linked_data/tests/unit/test_nice_http_client.py -q` either is gone or still
      passes against `contracts`

## 5. Principles and mapping docs paths

- [x] 5.1 Update `openspec/principles.md` module graph (contracts leaf; plugins/`parsing` ↛ harvester) and
      `docs/surface-quality-bar.md` path rows for `plugin_base` / `nice_http_client`; verify those files name
      `middleware.contracts`
- [x] 5.2 Update remaining spec/design prose that hard-codes `middleware.harvester.errors` or `harvester/plugin_base.py`
      (error-handling design, skipped-datasets design, harvest-report design) in this change if still stale after apply;
      verify `rg "middleware.harvester.errors" openspec/specs` only remains where still true for report helpers

## 6. Validation

- [x] 6.1 `openspec validate --change extract-plugin-contracts` succeeds
- [x] 6.2 `uv run ruff format --config ruff.toml middleware/` and `uv run ruff check --config ruff.toml` on touched
      paths succeed
- [x] 6.3
      `uv run pytest middleware/contracts middleware/harvester middleware/parsing middleware/inspire middleware/linked_data middleware/generic middleware/oai_pmh -q`
      (unit; skip marked integration unless already in default) succeeds
