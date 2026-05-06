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

5. **robots.txt state owned by `RobotsTxtCache`, held inside `NiceHttpClient`**
   — `NiceHttpClient` already owns the per-host locks and timing state required
   for rate limiting. `RobotsTxtCache` is a private helper class that stores
   per-host robots.txt parse results and `Crawl-delay` values; `NiceHttpClient`
   holds a single `RobotsTxtCache` instance and delegates all robots.txt logic
   to it. This keeps the context manager boundary clean while isolating cache
   state from connection management.

6. **`respect_robots_txt` defaults to `True` in `NiceHttpClientConfig`**
   — The safe default is to respect robots.txt for all plugins. Plugins that
   call machine-to-machine APIs where robots.txt is irrelevant are not affected
   because those plugins do not use `NiceHttpClient`.

7. **`RobotsTxtDisallowedError` signals a disallowed URL to the caller**
   — `NiceHttpClient.ensure_allowed()` raises `RobotsTxtDisallowedError`
   (a `RuntimeError` subclass) when a URL is forbidden. A dedicated exception
   type lets plugin code distinguish a robots.txt rejection from other HTTP
   errors with a single `except` clause, without inspecting error messages.
   The plugin converts it to a `RecordProcessingError` and continues with the
   remaining URLs (see req: "signal a disallow … so the caller can … skip").
