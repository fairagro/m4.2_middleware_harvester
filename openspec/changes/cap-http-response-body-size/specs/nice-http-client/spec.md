## ADDED Requirements

### Requirement: Configurable maximum HTTP response body size

The system SHALL provide `NiceHttpClientConfig.max_response_body_bytes` as a required-config field with an explicit
default of `33554432` (32 MiB) and `ge=1`. There MUST NOT be a hidden fallback outside this field.

#### Scenario: Default is 32 MiB

- **WHEN** an operator omits `max_response_body_bytes`
- **THEN** the effective limit is `33554432` bytes

#### Scenario: Operator override

- **WHEN** an operator sets `max_response_body_bytes` to a positive integer
- **THEN** that value is the limit used by `NiceHttpClient`

### Requirement: Reject oversized Content-Length before reading the body

When a response includes a `Content-Length` header whose integer value is greater than `max_response_body_bytes`, the
system SHALL fail the request with a clear body-too-large error **without** reading the response body.

#### Scenario: Content-Length over the limit

- **WHEN** a GET receives `Content-Length` larger than `max_response_body_bytes`
- **THEN** the client raises a body-too-large error and does not buffer the body

### Requirement: Stream the response body and stop when the limit is exceeded

The system SHALL read successful harvest GET response bodies incrementally. If cumulative bytes read would exceed
`max_response_body_bytes`, the system SHALL fail with a clear body-too-large error and MUST NOT retain more than the
configured limit plus at most one chunk of overshoot in memory for the check.

#### Scenario: Body grows past the limit without Content-Length

- **WHEN** a response has no usable `Content-Length` (or a smaller declared length) but streaming yields more than
  `max_response_body_bytes` bytes
- **THEN** the client raises a body-too-large error

#### Scenario: Body exactly at the limit succeeds

- **WHEN** a response body is exactly `max_response_body_bytes` bytes
- **THEN** the request succeeds and callers receive the full body

### Requirement: Body-too-large is not retried as a transient HTTP failure

The system SHALL NOT retry a request solely because the response body exceeded `max_response_body_bytes`. Transient
status retries (429/5xx) remain unchanged for responses that never hit the body-size limit.

#### Scenario: Oversized body does not consume retry_attempts as success path

- **WHEN** a response body exceeds the limit on the first attempt
- **THEN** the error is raised without treating the condition as a retryable transient HTTP status
