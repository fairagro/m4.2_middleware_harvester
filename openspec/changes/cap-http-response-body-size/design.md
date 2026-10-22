# Design

## Context

See proposal.md — Why. `NiceHttpClient.retry_get_with_client` uses `client.get()` and returns a fully buffered
`httpx.Response`. Robots.txt fetch uses the same client without the harvest GET helper. CSW goes through OWSLib.

## Goals / Non-Goals

**Goals:**

- One config knob on `NiceHttpClientConfig`, default 32 MiB (`33554432`), `ge=1`
- Enforce on harvest GETs (`get_with_policy` / `retry_get_with_client`)
- Clear typed or message-stable error for callers

**Non-Goals:**

- CSW/OWSLib enforcement in this change
- Changing robots.txt fetch semantics beyond optionally applying the same cap (prefer: apply the same limit so
  robots.txt cannot OOM either — small files; oversized robots.txt is still a DoS vector)

## Decisions

1. **Default 32 MiB** — Large enough for atypical ISO/JSON-LD pages; small enough to bound memory. Operators raise via
   config. Alternative: 10 MiB — tighter but may false-fail real catalogues; reject for default.

2. **Stream in `retry_get_with_client`** — Use `client.stream("GET", …)` (or `client.get` with streaming), check
   `Content-Length` when present, then `aiter_bytes` until done or over limit; build a Response with the collected bytes
   (or raise before allocating the full body). Prefer raising a dedicated `ResponseBodyTooLargeError(RuntimeError)` (or
   subclass of an existing contracts error) with URL + limit + observed size so plugins map it like other transport
   failures.

3. **Apply to robots.txt fetch too** — Same config, same helper or shared `_read_limited` — avoid a second unbounded
   path on the same client.

4. **CSW deferred in spec** — Document under `csw-harvesting`: body-size limiting SHALL NOT be claimed for OWSLib until
   a harvester-owned HTTP session exists (#355). No stub config field on inspire Config in this change.

5. **Harvest report** — Do not invent new report types. Rely on existing exception → `RecordProcessingError` /
   repository-issue paths in plugins/orchestrator. Verify at least one plugin path maps the new error without process
   crash (unit or existing pattern).

## Risks / Trade-offs

- [Streaming changes retry timing] → Keep retry on status/network errors; do not retry “body too large” as transient.
- [False positives on huge legitimate pages] → Configurable limit; default documented.
- [CSW still uncapped] → Accepted; recorded in spec; mitigated by chunked GetRecords + value bounds after parse.

## Migration Plan

1. Ship with default 32 MiB — existing YAML unchanged.
2. Operators with known large pages raise `http.max_response_body_bytes` (or nested `protocol.http` / plugin `http`).
