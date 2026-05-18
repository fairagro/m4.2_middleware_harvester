# NiceHttpClient

Shared HTTP client wrapper that centralizes all polite-harvesting behaviour for
plugins that make direct HTTP requests. Plugins embed `NiceHttpClientConfig`
instead of defining their own HTTP parameters. Robots.txt compliance is enabled
by default and can be disabled per plugin config.

## Requirements

- [ ] Provide `NiceHttpClientConfig` as a Pydantic `BaseModel` with fields:
  `user_agent`, `connect_timeout`, `read_timeout`, `max_connections`,
  `max_requests_per_second`, `retry_attempts`, `retry_backoff_base`,
  `retry_backoff_factor`, `max_retry_delay`, and `respect_robots_txt`
  (default `True`).
- [ ] `NiceHttpClient` is an async context manager; entering creates and
  configures the underlying HTTP connection pool, exiting releases the pool and
  all per-host state.
- [ ] Apply the configured `user_agent` as the `User-Agent` header on every
  outgoing request.
- [ ] Apply `connect_timeout` and `read_timeout` to every outgoing request.
- [ ] Limit the total number of concurrent connections to `max_connections`.
- [ ] Retry failed requests on HTTP 429, HTTP 5xx responses, and transient
  network errors using exponential backoff.
- [ ] When a `Retry-After` response header is present, wait the indicated
  duration before retrying; cap the wait at `max_retry_delay`.
- [ ] Cap locally calculated exponential backoff delays at `max_retry_delay`.
- [ ] When `retry_attempts = 0`, raise the error immediately without any retry
  attempt.
- [ ] When `max_requests_per_second` is set to a positive value, enforce
  per-host rate limiting so that no more than that many requests are sent to the
  same host per second.
- [ ] When `max_requests_per_second` is `None`, apply no host rate limiting.
- [ ] When `respect_robots_txt = True`: before the first request to any host,
  fetch and cache that host's `/robots.txt`; signal a disallow for any URL
  that is forbidden for the configured `user_agent` so the caller can log a
  warning and skip that URL while continuing to harvest the remaining URLs;
  apply the `Crawl-delay` directive from `robots.txt` as an additional
  per-host minimum delay, taking the larger of `Crawl-delay` and the delay
  derived from `max_requests_per_second`.
- [ ] When `respect_robots_txt = False`: perform no `robots.txt` fetch and no
  `robots.txt` check for any host.
- [ ] Plugin configs that use `NiceHttpClient` embed `NiceHttpClientConfig` as
  a nested `http` field and do not define individual HTTP parameters themselves.

## Edge Cases

`retry_attempts = 0` → raise on first failure; no retry is attempted.

`max_requests_per_second = None` → no host rate limiting; requests are sent
immediately.

`Retry-After` value exceeds `max_retry_delay` → wait exactly `max_retry_delay`,
then retry.

All `retry_attempts` exhausted → raise the last exception to the caller.

`robots.txt` fetch fails (network error or non-2xx response) → log a warning
and assume allow-all for that host; do not abort the harvest.

URL disallowed by `robots.txt` → caller logs a warning and skips the URL;
harvesting continues with the remaining URLs.

`respect_robots_txt = False` → no `robots.txt` request is ever made, regardless
of host.
