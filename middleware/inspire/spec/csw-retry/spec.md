# CSW Retry

Add transient-failure retry with exponential backoff to the `CSWClient` so that short-lived network interruptions do not abort a harvest run. Retry behaviour is controlled by four flat fields in `inspire.Config`.

## Requirements

- [ ] `inspire.Config` exposes four flat retry fields with the following defaults:
  - `retry_attempts: int = 5` (ge=0) — number of additional attempts after the first failure
  - `retry_backoff_base: float = 1.0` (gt=0) — initial delay in seconds
  - `retry_backoff_factor: float = 2.0` (ge=1) — exponential multiplier applied per attempt
  - `retry_max_delay: float = 600.0` (ge=0) — upper bound on any single inter-attempt wait
- [ ] `inspire.Config` exposes a `user_agent: str` field with default `"FAIRagro-Harvester/2.0 (dataservice@fairagro.org)"`.
- [ ] `CSWClient.connect()` forwards `user_agent` to `CatalogueServiceWeb` via `headers={"User-Agent": config.user_agent}`.
- [ ] The following `CSWClient` methods are retried on `OSError` or `TimeoutError`:
  - `connect()`
  - `_fetch_dc_ids()`
  - `_fetch_iso_batch()`
  - `get_record_count()`
- [ ] The inter-attempt delay is `retry_backoff_base × retry_backoff_factor^(attempt − 1)` with ±10% uniform jitter, capped at `retry_max_delay`.
- [ ] When `retry_attempts = 0`, the first failure propagates immediately without any retry.
- [ ] When all attempts are exhausted, the last exception is re-raised without wrapping.
- [ ] Each retry attempt is logged at WARNING level, including: method name, attempt number out of total, and the exception message.
- [ ] Retry logic applies only to the async path (`get_records_async`, `get_expected_datasets`). The synchronous `get_records()` path is not modified.
- [ ] `ValueError` is never retried; it propagates immediately regardless of `retry_attempts`.
- [ ] HTTP 4xx errors (e.g. 404 Not Found on `GetCapabilities`) are never retried; they propagate immediately. An error is treated as an HTTP 4xx error when it carries a `response.status_code` in the range 400–499.
- [ ] Inter-attempt sleep is performed with `asyncio.sleep()` so the event loop is not blocked.

## Edge Cases

`retry_attempts = 0` → exception propagates on first failure; no sleep occurs.

`OSError` on attempt N where N < `retry_attempts + 1` → log warning, sleep with jitter backoff, retry; on the final attempt → re-raise the exception.

`retry_backoff_base × retry_backoff_factor^(N−1)` exceeds `retry_max_delay` → wait exactly `retry_max_delay` (±10% jitter applied before the cap).

`ValueError` raised by OWSLib (e.g. malformed filter, schema mismatch) → propagates immediately; not retried.

`requests.exceptions.HTTPError` with a 4xx status code (e.g. 404 on `GetCapabilities`) → propagates immediately; not retried. `requests.exceptions.HTTPError` is a subclass of `IOError`/`OSError`, so without this guard it would be silently retried.

`connect()` fails on every attempt → `CswConnectionError` is raised from the last `OSError`/`TimeoutError`.
