# Spec Delta

## ADDED Requirements

### Requirement: Compressed responses MUST be decoded exactly once

When a response is served with `Content-Encoding: gzip` or `deflate`, the system MUST return the decoded body to
callers without decoding it a second time. The returned response MUST NOT carry `Content-Encoding` or
`Content-Length` headers, because its content is already decoded. `max_response_body_bytes` applies to the decoded
body size; the early `Content-Length` rejection is unchanged.

#### Scenario: Gzip response decodes

- **WHEN** a GET receives a 200 response with `Content-Encoding: gzip`
- **THEN** callers receive the decoded body and no decoding error is raised

#### Scenario: Deflate response decodes

- **WHEN** a GET receives a 200 response with `Content-Encoding: deflate`
- **THEN** callers receive the decoded body

#### Scenario: Returned response has no encoding headers

- **WHEN** a compressed response is returned to callers
- **THEN** it has no `Content-Encoding` and no `Content-Length` header

#### Scenario: Decoded size over the limit

- **WHEN** a compressed body is under `max_response_body_bytes` compressed but over it decoded
- **THEN** the client raises a body-too-large error

#### Scenario: Compressed transient error response

- **WHEN** a GET receives a 429 or 5xx response with `Content-Encoding: gzip`
- **THEN** the empty-body response has no encoding headers and retries behave as for any transient status
