# CSW Thread-Pool Isolation

## Purpose

Each `CSWClient` uses a dedicated, bounded `ThreadPoolExecutor` for blocking
OWSLib calls instead of the process-wide default executor. This prevents
thread-pool saturation when multiple INSPIRE repositories are harvested
concurrently and makes the concurrency limit explicit and configurable.

## Requirements

### Requirement: Per-client bounded ThreadPoolExecutor

`CSWClient` MUST own a `concurrent.futures.ThreadPoolExecutor` whose
`max_workers` is `Config.csw_thread_pool_size` (default `4`).

#### Scenario: Pool size from config

- **WHEN** a `CSWClient` is constructed with `csw_thread_pool_size` set to `N`
- **THEN** its executor is created with `max_workers=N`

### Requirement: Lazy executor creation

The executor MUST be created once on first use (first async method /
`__aenter__`), not eagerly in `__init__`.

#### Scenario: Unused client creates no pool

- **WHEN** a `CSWClient` is constructed but no async CSW work runs
- **THEN** no worker threads are started until the executor is first needed

### Requirement: Route blocking work through the owned executor

Every blocking OWSLib call inside `CSWClient` async paths MUST run via
`loop.run_in_executor(self._executor, …)` (or the client’s
`_run_in_executor` wrapper). The client MUST NOT use bare `asyncio.to_thread()`
for those calls, because `to_thread` always targets the process default pool.

#### Scenario: Async get_records uses owned pool

- **WHEN** `get_records_async` (or another async CSW method) performs OWSLib I/O
- **THEN** the work is submitted to the client-owned executor

### Requirement: Context-manager lifecycle and fallback shutdown

`CSWClient` MUST shut down its executor in `__aexit__`. When the client is not
used as a context manager (e.g. some unit tests), `__del__` MUST best-effort
shut down the executor to avoid leaking threads.

#### Scenario: async with cleans up

- **WHEN** code exits an `async with CSWClient(...)` block
- **THEN** the owned executor is shut down

#### Scenario: GC without context manager

- **WHEN** a client with a started executor is garbage-collected without
  `__aexit__`
- **THEN** `__del__` attempts executor shutdown

### Requirement: Edge case — serial pool and isolation

When `csw_thread_pool_size = 1`, all OWSLib calls for that client MUST be
serialised with no other behavioural change. Multiple `CSWClient` instances
(one per repository) MUST each hold their own executor so there is no
cross-repository thread contention on a shared pool.

#### Scenario: Size one serialises

- **WHEN** `csw_thread_pool_size` is `1`
- **THEN** concurrent async CSW calls for that client still share a single
  worker thread

#### Scenario: Separate clients are isolated

- **WHEN** two repositories each construct a `CSWClient`
- **THEN** each client has a distinct executor instance
