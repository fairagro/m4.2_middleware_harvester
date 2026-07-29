# CSW Thread-Pool Isolation

## Purpose

Each `CSWClient` uses a dedicated, bounded `ThreadPoolExecutor` for all
blocking OWSLib calls instead of the process-wide default executor.
This prevents thread-pool saturation when multiple INSPIRE repositories
are harvested concurrently and makes the concurrency limit explicit and
configurable.

## Requirements

### Requirement: CSWClient owns a concurrent.futures.ThreadPoolExecutor with a
The system SHALL ensure that `CSWClient` owns a `concurrent.futures.ThreadPoolExecutor` with a.

#### Scenario: Satisfies — CSWClient owns a concurrent.futures.ThreadPoolExecutor with a
- **WHEN** the conditions described by this requirement apply
- **THEN** `CSWClient` owns a `concurrent.futures.ThreadPoolExecutor` with a

### Requirement: The executor is created once when the first async method…
The executor SHALL be created once when the first async method is called.

#### Scenario: Satisfies — The executor is created once when the first async method…
- **WHEN** the conditions described by this requirement apply
- **THEN** The executor is created once when the first async method is called

### Requirement: Every asyncio.to_thread() call inside CSWClient is replaced by
The system SHALL ensure that every `asyncio.to_thread()` call inside `CSWClient` is replaced by.

#### Scenario: Satisfies — Every asyncio.to_thread() call inside CSWClient is replaced by
- **WHEN** the conditions described by this requirement apply
- **THEN** Every `asyncio.to_thread()` call inside `CSWClient` is replaced by

### Requirement: When CSWClient is not used as a context manager (e.g.…
The system SHALL ensure that when `CSWClient` is not used as a context manager (e.g. in tests or.

#### Scenario: Satisfies — When CSWClient is not used as a context manager (e.g.…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `CSWClient` is not used as a context manager (e.g. in tests or

### Requirement: Edge case — - csw_thread_pool_size = 1
The system SHALL handle this edge case: when - `csw_thread_pool_size = 1`, then all OWSLib calls for that client are serialised; no other behaviour changes. - Client is garbage-collected without `__aexit__` being called → executor is shut down via `__del__`; a `ResourceWarning` is emitted in debug mode to encourage proper context-manager usage. - Multiple `CSWClient` instances (one per repository) each hold their own executor → no cross-repository thread contention.

#### Scenario: Edge case — - csw_thread_pool_size = 1
- **WHEN** - `csw_thread_pool_size = 1`
- **THEN** all OWSLib calls for that client are serialised; no other behaviour changes. - Client is garbage-collected without `__aexit__` being called → executor is shut down via `__del__`; a `ResourceWarning` is emitted in debug mode to encourage proper context-manager usage. - Multiple `CSWClient` instances (one per repository) each hold their own executor → no cross-repository thread contention
