## 1. Pooled session module

- [x] 1.1 New `middleware/inspire/src/middleware/inspire/http_pooling.py`: thread-local `requests.Session` factory
      (`pool_connections=1, pool_maxsize=1`), a `_PooledOwslibRequests` shim exposing `.post` / `.get` / `.request`, and
      `install()` rebinding `owslib.util.requests` to it (called at import time)
- [x] 1.2 `run_pooled(loop, executor, fn, *args, **kwargs)` — registers the calling worker thread's session under
      `id(executor)` before running `fn`
- [x] 1.3 `close_pooled(executor)` — pops and best-effort closes every session registered for that executor
- [x] 1.4 `requests` added as a direct dependency in `middleware/inspire/pyproject.toml`; `uv.lock` refreshed

## 2. CSWClient wiring

- [x] 2.1 `csw_client.py`: import `run_pooled`, `close_pooled`; `_run_in_executor` calls `run_pooled(...)` instead of
      `loop.run_in_executor(...)` directly
- [x] 2.2 `_shutdown_executor` calls `close_pooled(executor)` after `executor.shutdown(wait=False)`
- [x] 2.3 Net line-count change to `csw_client.py` stays within pylint's `max-module-lines` ceiling (verified: exactly
      1000 lines, `pylint` rates it 10.00/10 with no `too-many-lines`)

## 3. Tests

- [x] 3.1 New `middleware/inspire/tests/unit/test_http_pooling.py`: `install()` rebinds and is idempotent; shim methods
      forward to the thread-local session; one thread reuses one session across repeated calls; distinct threads get
      distinct sessions; `close_pooled` closes + forgets one executor's sessions without touching a second, concurrently
      active executor's sessions; closing an executor that never ran any work is a no-op
- [x] 3.2 `test_csw_client.py`: context-manager shutdown calls `close_pooled(executor)`; `_run_in_executor` dispatches
      through `run_pooled` with the expected executor/fn/args
- [x] 3.3 Existing `test_csw_client.py` / `test_csw_client_paging.py` / `test_xml_hardening.py` suites still pass
      unmodified (mock-based `run_in_executor` side effects are compatible with the `call()` closure `run_pooled`
      submits)

## 4. Validation

- [x] 4.1 `uv run pytest -m "not integration and not system_local and not system_external"` green (full repo: 483
      passed)
- [x] 4.2 `bash scripts/run-quality-cli.sh mypy --config-file mypy.ini middleware/` clean
- [x] 4.3 `uv run ruff format --check` / `bash scripts/run-quality-cli.sh pylint --rcfile .pylintrc middleware/` clean
      for touched files (pylint 9.96/10 overall, pre-existing unrelated `E0401` test-helper import noise only — see
      `run-ci-equivalent-quality-checks` note on local-only lint noise)
- [x] 4.4 `bash scripts/run-quality-cli.sh bandit -c pyproject.toml -r middleware/inspire/src` clean (one pre-existing,
      unrelated low-severity finding at `csw_client.py:988`, not touched by this change)
- [x] 4.5 `openspec validate 2026-09-28-pool-csw-http-sessions --strict`
