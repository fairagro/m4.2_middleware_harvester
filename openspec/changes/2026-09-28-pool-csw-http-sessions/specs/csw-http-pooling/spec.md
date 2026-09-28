## Purpose

Reduces the connection-setup cost of INSPIRE CSW harvesting by pooling and reusing HTTP connections across the pages,
DC-fallback requests and capability probes of a single harvest, instead of opening a new TCP + TLS connection for every
OWSLib call.

## ADDED Requirements

### Requirement: The INSPIRE package installs a pooled-session stand-in for OWSLib's functional requests API

The system SHALL rebind the module-level name `owslib.util.requests` to a stand-in object when
`middleware.inspire.http_pooling` is imported. The stand-in SHALL expose `.post`, `.get` and `.request` methods matching
the call signature of the corresponding functions in the `requests` module, and SHALL forward each call to a pooled
`requests.Session` associated with the calling thread. Installation SHALL NOT modify the global `requests` module or any
other name.

#### Scenario: OWSLib calls are pooled

- **WHEN** OWSLib performs a `GetRecords`, `GetCapabilities` or `DescribeRecord` call via `http_post`, `http_get` or
  `openURL`
- **THEN** the underlying HTTP call is dispatched through a `requests.Session`, not a fresh unpooled request

#### Scenario: Other requests consumers are unaffected

- **WHEN** code outside `owslib.util` (e.g. another dependency importing `requests` directly) makes an HTTP call
- **THEN** that call is unaffected by the stand-in and uses the stock `requests` module

### Requirement: One pooled session per worker thread

The system SHALL maintain at most one `requests.Session` per thread, created lazily on that thread's first CSW HTTP call
and reused for every subsequent call from the same thread. The system SHALL NOT share one `requests.Session` object
across multiple threads.

#### Scenario: Sequential calls on one thread reuse the same session

- **WHEN** a single worker thread performs multiple CSW HTTP calls in sequence
- **THEN** every call after the first reuses the same `requests.Session` object created by the first call

#### Scenario: Different threads never share a session

- **WHEN** two different worker threads each perform a CSW HTTP call
- **THEN** each thread is associated with its own distinct `requests.Session` object

### Requirement: Pooled sessions are tracked per owning executor and closed on CSWClient shutdown

The system SHALL associate every pooled session with the `ThreadPoolExecutor` whose worker thread created it. When
`CSWClient` shuts down its owned executor, the system SHALL close every session associated with that executor and SHALL
NOT close sessions associated with any other executor.

#### Scenario: CSWClient shutdown closes its own sessions

- **WHEN** a `CSWClient` instance exits its async context (or is torn down via the `__del__` fallback) after performing
  CSW HTTP calls
- **THEN** every pooled session created by that instance's worker threads is closed

#### Scenario: Concurrent CSWClient instances do not close each other's sessions

- **GIVEN** two `CSWClient` instances harvesting concurrently, each with its own executor and pooled sessions
- **WHEN** one instance shuts down
- **THEN** the other instance's pooled sessions remain open and usable

#### Scenario: Shutting down a client that performed no CSW calls is a no-op

- **WHEN** a `CSWClient` instance's executor is shut down without any CSW HTTP call having been made
- **THEN** shutdown completes without error and closes no sessions

### Requirement: Pooling does not alter per-request TLS or authentication behaviour

The system SHALL forward `verify`, `cert`, `auth` and all other per-call keyword arguments supplied by OWSLib unchanged
to the pooled session's request methods. Pooling SHALL NOT change the effective TLS verification or authentication
behaviour of any CSW request, per `openspec/specs/csw-ssl-verify/`.

#### Scenario: verify_ssl behaviour is unchanged

- **WHEN** `CSWClient` connects with a given `inspire.Config.verify_ssl` value
- **THEN** every CSW HTTP request carries the same effective `verify` behaviour as it would without session pooling
