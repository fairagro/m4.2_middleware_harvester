# CSW Thread-Pool Isolation — Design

## Module Overview

```text
CSWClient
├── _executor: ThreadPoolExecutor   # owned, bounded
├── __aenter__ / __aexit__          # lifecycle management
├── __del__                         # fallback shutdown
└── _run_in_executor(fn, *args)     # thin wrapper used by all async methods
```

`Config.csw_thread_pool_size` controls the maximum number of worker threads
per client instance.

## Key Decisions

1. **Per-client executor instead of the global default executor**
   — `asyncio.to_thread()` submits work to the process-wide
   `ThreadPoolExecutor`, whose size defaults to `min(32, cpu_count()+4)`.
   Under high concurrency this pool is shared with all other async code in
   the process. A per-client executor gives each `CSWClient` an explicit,
   bounded resource budget and prevents one slow CSW endpoint from
   exhausting threads needed by other concurrent tasks.

2. **`loop.run_in_executor(self._executor, fn, *args)` instead of
   `asyncio.to_thread()`**
   — `asyncio.to_thread()` does not accept a custom executor argument.
   `loop.run_in_executor(executor, fn, *args)` is the standard asyncio API
   for submitting work to a specific pool. It is the only way to route
   blocking calls away from the default executor.

3. **Lazy executor creation on first use, not in `__init__`**
   — Creating the executor in `__init__` would start threads before any
   async work is needed, which wastes resources when `CSWClient` is
   constructed but `get_records_async()` is never called (e.g. in unit
   tests that only exercise the sync `get_records()` path).

4. **`csw_thread_pool_size` as a `Config` field with default `4`**
   — Four threads per client is sufficient for the expected `<10`
   concurrent CSW repositories, keeps the total thread budget well within
   the OS default limit, and avoids a magic number in the source.
   The field follows the same `ConfigBase` override convention as existing
   fields so operators can tune it without a code change.

5. **`__del__` as a fallback, `ResourceWarning` in debug mode**
   — Relying on `__del__` alone for cleanup is fragile, but omitting it
   would leak the thread pool if callers forget `async with`. The warning
   nudges developers towards the context-manager pattern without making
   non-context-manager use a hard error (some callers, e.g. unit tests,
   construct `CSWClient` outside a context manager intentionally).
