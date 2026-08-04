# CSW Retry

## Purpose

Add transient-failure retry with exponential backoff to the `CSWClient` so that short-lived network interruptions do not abort a harvest run. Retry behaviour is controlled by four flat fields in `inspire.Config`.

## Requirements

### Requirement: Inspire.Config exposes four flat retry fields with the following defaults:
The system SHALL ensure that `inspire.Config` exposes four flat retry fields with the following defaults:.

#### Scenario: Satisfies — Inspire.Config exposes four flat retry fields with the following defaults:
- **WHEN** the conditions described by this requirement apply
- **THEN** `inspire.Config` exposes four flat retry fields with the following defaults:

### Requirement: Inspire.Config exposes a user_agent: str field with default "FAIRagro-Harvester/2.0 (harvestmaster@fairagro.net)"
The system SHALL ensure that `inspire.Config` exposes a `user_agent: str` field with default `"FAIRagro-Harvester/2.0 (harvestmaster@fairagro.net)"`.

#### Scenario: Satisfies — Inspire.Config exposes a user_agent: str field with default "FAIRagro-Harvester/2.0 (harvestmaster@fairagro.net)"
- **WHEN** the conditions described by this requirement apply
- **THEN** `inspire.Config` exposes a `user_agent: str` field with default `"FAIRagro-Harvester/2.0 (harvestmaster@fairagro.net)"`

### Requirement: CSWClient.connect() forwards user_agent to CatalogueServiceWeb via headers={"User-Agent": config.user_agent}
The system SHALL ensure that `CSWClient.connect()` forwards `user_agent` to `CatalogueServiceWeb` via `headers={"User-Agent": config.user_agent}`.

#### Scenario: Satisfies — CSWClient.connect() forwards user_agent to CatalogueServiceWeb via headers={"User-Agent": config.user_agent}
- **WHEN** the conditions described by this requirement apply
- **THEN** `CSWClient.connect()` forwards `user_agent` to `CatalogueServiceWeb` via `headers={"User-Agent": config.user_agent}`

### Requirement: The following CSWClient methods are retried on OSError or TimeoutError:
The following `CSWClient` methods SHALL be retried on `OSError` or `TimeoutError`:.

#### Scenario: Satisfies — The following CSWClient methods are retried on OSError or TimeoutError:
- **WHEN** the conditions described by this requirement apply
- **THEN** The following `CSWClient` methods are retried on `OSError` or `TimeoutError`:

### Requirement: The inter-attempt delay is retry_backoff_base × retry_backoff_factor^(attempt − 1) with…
The inter-attempt delay SHALL be `retry_backoff_base × retry_backoff_factor^(attempt − 1)` with ±10% uniform jitter, capped at `retry_max_delay`.

#### Scenario: Satisfies — The inter-attempt delay is retry_backoff_base × retry_backoff_factor^(attempt − 1) with…
- **WHEN** the conditions described by this requirement apply
- **THEN** The inter-attempt delay is `retry_backoff_base × retry_backoff_factor^(attempt − 1)` with ±10% uniform jitter, capped at `retry_max_delay`

### Requirement: When retry_attempts = 0, the first failure propagates immediately without…
The system SHALL ensure that when `retry_attempts = 0`, the first failure propagates immediately without any retry.

#### Scenario: Satisfies — When retry_attempts = 0, the first failure propagates immediately without…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `retry_attempts = 0`, the first failure propagates immediately without any retry

### Requirement: When all attempts are exhausted, the last exception is re-raised…
The system SHALL ensure that when all attempts are exhausted, the last exception is re-raised without wrapping.

#### Scenario: Satisfies — When all attempts are exhausted, the last exception is re-raised…
- **WHEN** the conditions described by this requirement apply
- **THEN** When all attempts are exhausted, the last exception is re-raised without wrapping

### Requirement: Each retry attempt is logged at WARNING level, including: method…
The system SHALL ensure that each retry attempt is logged at WARNING level, including: method name, attempt number out of total, and the exception message.

#### Scenario: Satisfies — Each retry attempt is logged at WARNING level, including: method…
- **WHEN** the conditions described by this requirement apply
- **THEN** Each retry attempt is logged at WARNING level, including: method name, attempt number out of total, and the exception message

### Requirement: Retry logic applies only to the async path (get_records_async, get_expected_datasets).…
The system SHALL retry logic applies only to the async path (`get_records_async`, `get_expected_datasets`). The synchronous `get_records()` path is not modified.

#### Scenario: Satisfies — Retry logic applies only to the async path (get_records_async, get_expected_datasets).…
- **WHEN** the conditions described by this requirement apply
- **THEN** Retry logic applies only to the async path (`get_records_async`, `get_expected_datasets`). The synchronous `get_records()` path is not modified

### Requirement: ValueError is never retried; it propagates immediately regardless of retry_attempts
The system SHALL ensure that `ValueError` is never retried; it propagates immediately regardless of `retry_attempts`.

#### Scenario: Satisfies — ValueError is never retried; it propagates immediately regardless of retry_attempts
- **WHEN** the conditions described by this requirement apply
- **THEN** `ValueError` is never retried; it propagates immediately regardless of `retry_attempts`

### Requirement: HTTP 4xx errors (e.g. 404 Not Found on GetCapabilities) are…
The system SHALL NOT retry HTTP 4xx errors (e.g. 404 Not Found on `GetCapabilities`); they propagate immediately. An error is treated as an HTTP 4xx error when it carries a `response.status_code` in the range 400–499.

#### Scenario: Satisfies — HTTP 4xx errors (e.g. 404 Not Found on GetCapabilities) are…
- **WHEN** the conditions described by this requirement apply
- **THEN** HTTP 4xx errors (e.g. 404 Not Found on `GetCapabilities`) are never retried; they propagate immediately. An error is treated as an HTTP 4xx error when it carries a `response.status_code` in the range 400–499

### Requirement: Inter-attempt sleep is performed with asyncio.sleep() so the event loop…
The system SHALL perform inter-attempt sleep with `asyncio.sleep()` so the event loop is not blocked.

#### Scenario: Satisfies — Inter-attempt sleep is performed with asyncio.sleep() so the event loop…
- **WHEN** the conditions described by this requirement apply
- **THEN** Inter-attempt sleep is performed with `asyncio.sleep()` so the event loop is not blocked

### Requirement: Edge case — Retry_attempts = 0
The system SHALL handle this edge case: when `retry_attempts = 0`, then exception propagates on first failure; no sleep occurs.

#### Scenario: Edge case — Retry_attempts = 0
- **WHEN** `retry_attempts = 0`
- **THEN** exception propagates on first failure; no sleep occurs

### Requirement: Edge case — OSError on attempt N where N < retry_attempts + 1
The system SHALL handle this edge case: when `OSError` on attempt N where N < `retry_attempts + 1`, then log warning, sleep with jitter backoff, retry; on the final attempt → re-raise the exception.

#### Scenario: Edge case — OSError on attempt N where N < retry_attempts + 1
- **WHEN** `OSError` on attempt N where N < `retry_attempts + 1`
- **THEN** log warning, sleep with jitter backoff, retry; on the final attempt → re-raise the exception

### Requirement: Edge case — Retry_backoff_base × retry_backoff_factor^(N−1) exceeds retry_max_delay
The system SHALL handle this edge case: when `retry_backoff_base × retry_backoff_factor^(N−1)` exceeds `retry_max_delay`, then wait exactly `retry_max_delay` (±10% jitter applied before the cap).

#### Scenario: Edge case — Retry_backoff_base × retry_backoff_factor^(N−1) exceeds retry_max_delay
- **WHEN** `retry_backoff_base × retry_backoff_factor^(N−1)` exceeds `retry_max_delay`
- **THEN** wait exactly `retry_max_delay` (±10% jitter applied before the cap)

### Requirement: Edge case — ValueError raised by OWSLib (e.g. malformed filter, schema mismatch)
The system SHALL handle this edge case: when `ValueError` raised by OWSLib (e.g. malformed filter, schema mismatch), then propagates immediately; not retried.

#### Scenario: Edge case — ValueError raised by OWSLib (e.g. malformed filter, schema mismatch)
- **WHEN** `ValueError` raised by OWSLib (e.g. malformed filter, schema mismatch)
- **THEN** propagates immediately; not retried

### Requirement: Edge case — Requests.exceptions.HTTPError with a 4xx status code (e.g. 404 on GetCapabilities)
The system SHALL handle this edge case: when `requests.exceptions.HTTPError` with a 4xx status code (e.g. 404 on `GetCapabilities`), then propagates immediately; not retried. `requests.exceptions.HTTPError` is a subclass of `IOError`/`OSError`, so without this guard it would be silently retried.

#### Scenario: Edge case — Requests.exceptions.HTTPError with a 4xx status code (e.g. 404 on GetCapabilities)
- **WHEN** `requests.exceptions.HTTPError` with a 4xx status code (e.g. 404 on `GetCapabilities`)
- **THEN** propagates immediately; not retried. `requests.exceptions.HTTPError` is a subclass of `IOError`/`OSError`, so without this guard it would be silently retried

### Requirement: Edge case — Connect() fails on every attempt
The system SHALL handle this edge case: when `connect()` fails on every attempt, then `CswConnectionError` is raised from the last `OSError`/`TimeoutError`.

#### Scenario: Edge case — Connect() fails on every attempt
- **WHEN** `connect()` fails on every attempt
- **THEN** `CswConnectionError` is raised from the last `OSError`/`TimeoutError`
