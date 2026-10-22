# Proposal

## Why

No HTTP path limits response body size; the full body is buffered before parse/validation. Read timeouts do not stop a
fast endpoint from sending large payloads. #20 / #382 left this to the transport layer. Partner RDI endpoints are
operator-configured and treated as untrusted input (`openspec/principles.md` — Security by default).

## What Changes

- Add configurable `max_response_body_bytes` on `NiceHttpClientConfig` (default **32 MiB**, no hidden fallback).
- `NiceHttpClient` enforces the limit: reject oversized `Content-Length` before reading; stream the body and fail with a
  clear error if the cumulative size exceeds the limit.
- Oversized responses surface as harvest failures (record or repository issue) without crashing the run — via existing
  error mapping where callers already handle HTTP failures.
- Document that the INSPIRE CSW / OWSLib `requests` path does **not** get the same cap in this change (no
  harvester-owned session; CSW HTTP pooling deferred in #355). Follow-up when pooling lands.

**Non-goals:** Implementing CSW body caps now. Changing value-bounds (#382). Reworking OWSLib.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `nice-http-client`: Configurable max response body size; stream + Content-Length enforcement.
- `csw-harvesting`: Record that body-size limiting is out of scope for OWSLib until owned HTTP transport exists.

## Impact

- `middleware/contracts` (`NiceHttpClientConfig`, `NiceHttpClient` / `retry_get_with_client`)
- Unit tests under `middleware/contracts`
- Call sites that already catch `httpx` / client errors continue to map failures into the harvest report
- OpenSpec: `nice-http-client`, `csw-harvesting`
