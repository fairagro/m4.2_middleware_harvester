# CSW Retry — Design

## Architecture

`CSWClient` gains a private async helper method `_retry(fn, *args)` that:

1. Calls `asyncio.to_thread(fn, *args)`.
2. On `OSError` or `TimeoutError`, logs a WARNING and sleeps the computed backoff delay.
3. Repeats up to `config.retry_attempts` additional times.
4. Re-raises the last exception if all attempts fail.

The four affected callsites — `connect()`, `_fetch_dc_ids()`, `_fetch_iso_batch()`, and `get_record_count()` — delegate their `asyncio.to_thread(...)` calls to `_retry(...)` instead.

```text
get_records_async / get_expected_datasets
    │
    └─ CSWClient._retry(self.connect)
    └─ CSWClient._retry(self._fetch_dc_ids_sync, ...)
    └─ CSWClient._retry(self._fetch_iso_batch_sync, ...)
    └─ CSWClient._retry(self.get_record_count)
           │
           ├─ asyncio.to_thread(fn, *args)   ← attempt 1
           ├─ asyncio.sleep(backoff)          ← on OSError/TimeoutError
           ├─ asyncio.to_thread(fn, *args)   ← attempt 2
           └─ ...
```

## Key Decisions

1. **Flat fields in `inspire.Config`, not `NiceHttpClientConfig`**
   — `NiceHttpClientConfig` also carries `user_agent`, `connect_timeout`, `read_timeout`, `max_connections`, `max_requests_per_second`, and `respect_robots_txt`, none of which are applicable to OWSLib. OWSLib manages its own `requests`-based HTTP stack and exposes no hook for those values. Embedding all of `NiceHttpClientConfig` would expose semantically inert fields that would confuse operators inspecting the YAML configuration. Flat fields carry only what CSWClient can actually use.

2. **`user_agent` forwarded via `headers={"User-Agent": ...}` at `CatalogueServiceWeb` construction**
   — OWSLib stores the `headers` dict on the instance and merges it into every subsequent request (overriding the default `User-Agent: OWSLib (...)` on POST paths, and used directly on GET paths). One-time injection at construction is therefore sufficient to cover all CSW calls for the lifetime of the client.

3. **Retry at the `asyncio.to_thread()` boundary, not inside the synchronous thread**
   — OWSLib is entirely synchronous. Placing the retry loop in the async layer means backoff sleeps use `asyncio.sleep()`, which yields the event loop during the wait. A blocking `time.sleep()` inside the synchronous thread would stall the event loop for the full backoff duration and prevent other coroutines from progressing.

4. **Only `OSError` and `TimeoutError` are retried — but HTTP 4xx errors are excluded**
   — These exception types map directly to transient network conditions: TCP resets, DNS resolution failures, and socket timeouts. `ValueError` signals a semantically incorrect request (e.g. a conflicting filter or a malformed URL); retrying an invalid request cannot succeed and must not be attempted.
   — `requests.exceptions.HTTPError` (raised by OWSLib on non-2xx responses) is a subclass of `IOError`/`OSError`, so without an explicit guard it would be retried. HTTP 4xx errors (e.g. 404 Not Found on `GetCapabilities`) are permanent server-side rejections and must propagate immediately. Detection is duck-typed via `getattr(exc, "response", None).status_code` — no direct `requests` import is needed, keeping the coupling to OWSLib's transport layer minimal.

5. **Synchronous `get_records()` path is not modified**
   — The plugin exclusively calls `get_records_async()`. Adding blocking retry (`time.sleep()`) to the synchronous path would harm callers that do not expect long stalls and would introduce a second, inconsistent retry implementation with no current use case.
