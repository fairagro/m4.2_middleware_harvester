# NiceHttpClient — Design

## Architecture

`NiceHttpClientConfig` is a standalone Pydantic `BaseModel` that holds all HTTP
politeness parameters. Plugin-specific config classes (e.g.
`middleware.schema_org.Config`) embed it as a nested `http` field; they do not
define individual HTTP parameters themselves.

`NiceHttpClient` is an async context manager that wraps an
`httpx.AsyncClient`. It owns all per-host runtime state: the connection pool,
per-host `asyncio.Lock` instances for rate limiting, per-host last-request
timestamps, and — when `respect_robots_txt = True` — per-host robots.txt parse
results and `Crawl-delay` values.

## Key Decisions

1. **Async context manager**
   — The context manager boundary guarantees that the connection pool and all
   per-host locks are released when the plugin's `run()` method exits, whether
   normally or via exception. Callers never need to close the client manually.

2. **`NiceHttpClientConfig` embedded as `http` field in plugin configs**
   — Each plugin config that uses direct HTTP embeds one `NiceHttpClientConfig`
   instance. This avoids duplicating field definitions and descriptions across
   config classes and gives a single place to document and validate all HTTP
   politeness parameters.

3. **Per-host rate limiting via `asyncio.Lock`**
   — A per-host lock serialises requests to the same host and enforces the
   minimum inter-request interval derived from `max_requests_per_second` and,
   when applicable, the `Crawl-delay` from `robots.txt`. Requests to different
   hosts proceed concurrently without interference.

4. **`Retry-After` takes priority over local backoff; both capped by `max_retry_delay`**
   — When a server signals its preferred retry interval via `Retry-After`, that
   value is used in preference to locally calculated exponential backoff.
   `max_retry_delay` caps both sources so a misbehaving server cannot stall the
   harvest indefinitely.

5. **robots.txt state merged into `NiceHttpClient` (supersedes `RobotsTxtCache`)**
   — `NiceHttpClient` already owns the per-host locks and timing state required
   for rate limiting. Merging robots.txt cache and `Crawl-delay` values into the
   same object avoids a separate `RobotsTxtCache` class and the indirection of
   passing it alongside the HTTP client. The standalone `RobotsTxtCache` class
   is superseded by this design.

6. **`respect_robots_txt` defaults to `True` in `NiceHttpClientConfig`**
   — The safe default is to respect robots.txt for all plugins. Plugins that
   call machine-to-machine APIs (e.g. CSW endpoints) where robots.txt is
   irrelevant are not affected because the inspire plugin does not use
   `NiceHttpClient` at all.
