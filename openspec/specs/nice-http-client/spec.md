# NiceHttpClient

## Purpose

Shared HTTP client wrapper that centralises all polite-harvesting behaviour for
plugins that make direct HTTP requests. Plugins embed `NiceHttpClientConfig`
instead of defining their own HTTP parameters. Robots.txt compliance is enabled
by default and can be disabled per plugin config.

## Requirements

### Requirement: Provide NiceHttpClientConfig as a Pydantic BaseModel with fields:
The system SHALL provide `NiceHttpClientConfig` as a Pydantic `BaseModel` with fields:.

#### Scenario: Satisfies — Provide NiceHttpClientConfig as a Pydantic BaseModel with fields:
- **WHEN** the conditions described by this requirement apply
- **THEN** The system SHALL provide `NiceHttpClientConfig` as a Pydantic `BaseModel` with fields:

### Requirement: NiceHttpClient is an async context manager; entering creates and
The system SHALL ensure that `NiceHttpClient` is an async context manager; entering creates and.

#### Scenario: Satisfies — NiceHttpClient is an async context manager; entering creates and
- **WHEN** the conditions described by this requirement apply
- **THEN** `NiceHttpClient` is an async context manager; entering creates and

### Requirement: Apply the configured user_agent as the User-Agent header on every
The system SHALL apply the configured `user_agent` as the `User-Agent` header on every.

#### Scenario: Satisfies — Apply the configured user_agent as the User-Agent header on every
- **WHEN** the conditions described by this requirement apply
- **THEN** Apply the configured `user_agent` as the `User-Agent` header on every

### Requirement: Apply connect_timeout and read_timeout to every outgoing request
The system SHALL apply `connect_timeout` and `read_timeout` to every outgoing request.

#### Scenario: Satisfies — Apply connect_timeout and read_timeout to every outgoing request
- **WHEN** the conditions described by this requirement apply
- **THEN** Apply `connect_timeout` and `read_timeout` to every outgoing request

### Requirement: Limit the total number of concurrent connections to max_connections
The system SHALL limit the total number of concurrent connections to `max_connections`.

#### Scenario: Satisfies — Limit the total number of concurrent connections to max_connections
- **WHEN** the conditions described by this requirement apply
- **THEN** Limit the total number of concurrent connections to `max_connections`

### Requirement: Retry failed requests on HTTP 429, HTTP 5xx responses, and…
The system SHALL retry failed requests on HTTP 429, HTTP 5xx responses, and transient.

#### Scenario: Satisfies — Retry failed requests on HTTP 429, HTTP 5xx responses, and…
- **WHEN** the conditions described by this requirement apply
- **THEN** Retry failed requests on HTTP 429, HTTP 5xx responses, and transient

### Requirement: When a Retry-After response header is present, wait the indicated
The system SHALL ensure that when a `Retry-After` response header is present, wait the indicated.

#### Scenario: Satisfies — When a Retry-After response header is present, wait the indicated
- **WHEN** the conditions described by this requirement apply
- **THEN** When a `Retry-After` response header is present, wait the indicated

### Requirement: Cap locally calculated exponential backoff delays at max_retry_delay
The system SHALL cap locally calculated exponential backoff delays at `max_retry_delay`.

#### Scenario: Satisfies — Cap locally calculated exponential backoff delays at max_retry_delay
- **WHEN** the conditions described by this requirement apply
- **THEN** Cap locally calculated exponential backoff delays at `max_retry_delay`

### Requirement: When retry_attempts = 0, raise the error immediately without any…
The system SHALL ensure that when `retry_attempts = 0`, raise the error immediately without any retry.

#### Scenario: Satisfies — When retry_attempts = 0, raise the error immediately without any…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `retry_attempts = 0`, raise the error immediately without any retry

### Requirement: When max_requests_per_second is set to a positive value, enforce
The system SHALL ensure that when `max_requests_per_second` is set to a positive value, enforce.

#### Scenario: Satisfies — When max_requests_per_second is set to a positive value, enforce
- **WHEN** the conditions described by this requirement apply
- **THEN** When `max_requests_per_second` is set to a positive value, enforce

### Requirement: When max_requests_per_second is None, apply no host rate limiting
The system SHALL ensure that when `max_requests_per_second` is `None`, apply no host rate limiting.

#### Scenario: Satisfies — When max_requests_per_second is None, apply no host rate limiting
- **WHEN** the conditions described by this requirement apply
- **THEN** When `max_requests_per_second` is `None`, apply no host rate limiting

### Requirement: When respect_robots_txt = True: before the first request to any…
The system SHALL ensure that when `respect_robots_txt = True`: before the first request to any host,.

#### Scenario: Satisfies — When respect_robots_txt = True: before the first request to any…
- **WHEN** the conditions described by this requirement apply
- **THEN** When `respect_robots_txt = True`: before the first request to any host,

### Requirement: When respect_robots_txt = False: perform no robots.txt fetch and no
The system SHALL ensure that when `respect_robots_txt = False`: perform no `robots.txt` fetch and no.

#### Scenario: Satisfies — When respect_robots_txt = False: perform no robots.txt fetch and no
- **WHEN** the conditions described by this requirement apply
- **THEN** When `respect_robots_txt = False`: perform no `robots.txt` fetch and no

### Requirement: Plugin configs that use NiceHttpClient embed NiceHttpClientConfig as
The system SHALL embed `NiceHttpClientConfig` in plugin configs that use `NiceHttpClient` as.

#### Scenario: Satisfies — Plugin configs that use NiceHttpClient embed NiceHttpClientConfig as
- **WHEN** the conditions described by this requirement apply
- **THEN** Plugin configs that use `NiceHttpClient` embed `NiceHttpClientConfig` as

### Requirement: Edge case — Retry_attempts = 0
The system SHALL handle this edge case: when `retry_attempts = 0`, then raise on first failure; no retry is attempted.

#### Scenario: Edge case — Retry_attempts = 0
- **WHEN** `retry_attempts = 0`
- **THEN** raise on first failure; no retry is attempted

### Requirement: Edge case — Max_requests_per_second = None
The system SHALL handle this edge case: when `max_requests_per_second = None`, then no host rate limiting; requests are sent immediately.

#### Scenario: Edge case — Max_requests_per_second = None
- **WHEN** `max_requests_per_second = None`
- **THEN** no host rate limiting; requests are sent immediately

### Requirement: Edge case — Retry-After value exceeds max_retry_delay
The system SHALL handle this edge case: when `Retry-After` value exceeds `max_retry_delay`, then wait exactly `max_retry_delay`, then retry.

#### Scenario: Edge case — Retry-After value exceeds max_retry_delay
- **WHEN** `Retry-After` value exceeds `max_retry_delay`
- **THEN** wait exactly `max_retry_delay`, then retry

### Requirement: Edge case — All retry_attempts exhausted
The system SHALL handle this edge case: when All `retry_attempts` exhausted, then raise the last exception to the caller.

#### Scenario: Edge case — All retry_attempts exhausted
- **WHEN** All `retry_attempts` exhausted
- **THEN** raise the last exception to the caller

### Requirement: Edge case — Robots.txt fetch fails (network error or non-2xx response)
The system SHALL handle this edge case: when `robots.txt` fetch fails (network error or non-2xx response), then log a warning and assume allow-all for that host; do not abort the harvest.

#### Scenario: Edge case — Robots.txt fetch fails (network error or non-2xx response)
- **WHEN** `robots.txt` fetch fails (network error or non-2xx response)
- **THEN** log a warning and assume allow-all for that host; do not abort the harvest

### Requirement: Edge case — URL disallowed by robots.txt
The system SHALL handle this edge case: when URL disallowed by `robots.txt`, then caller logs a warning and skips the URL; harvesting continues with the remaining URLs.

#### Scenario: Edge case — URL disallowed by robots.txt
- **WHEN** URL disallowed by `robots.txt`
- **THEN** caller logs a warning and skips the URL; harvesting continues with the remaining URLs

### Requirement: Edge case — Respect_robots_txt = False
The system SHALL handle this edge case: when `respect_robots_txt = False`, then no `robots.txt` request is ever made, regardless of host.

#### Scenario: Edge case — Respect_robots_txt = False
- **WHEN** `respect_robots_txt = False`
- **THEN** no `robots.txt` request is ever made, regardless of host
