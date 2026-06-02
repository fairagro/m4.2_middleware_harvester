# CSW Thread-Pool Isolation

Each `CSWClient` uses a dedicated, bounded `ThreadPoolExecutor` for all
blocking OWSLib calls instead of the process-wide default executor.
This prevents thread-pool saturation when multiple INSPIRE repositories
are harvested concurrently and makes the concurrency limit explicit and
configurable.

## Requirements

- [ ] `CSWClient` owns a `concurrent.futures.ThreadPoolExecutor` with a
      configurable maximum worker count (`csw_thread_pool_size`).
- [ ] The executor is created once when the first async method is called
      and shut down gracefully when the client is used as an async context
      manager (`__aenter__` / `__aexit__`).
- [ ] Every `asyncio.to_thread()` call inside `CSWClient` is replaced by
      `loop.run_in_executor(self._executor, ...)` so that all blocking OWSLib
      work runs in the client's own pool.
- [ ] When `CSWClient` is not used as a context manager (e.g. in tests or
      synchronous callers), the executor is shut down when the client is
      garbage-collected (`__del__`).

## Edge Cases

- `csw_thread_pool_size = 1` → all OWSLib calls for that client are
  serialised; no other behaviour changes.
- Client is garbage-collected without `__aexit__` being called → executor
  is shut down via `__del__`; a `ResourceWarning` is emitted in debug mode
  to encourage proper context-manager usage.
- Multiple `CSWClient` instances (one per repository) each hold their own
  executor → no cross-repository thread contention.
