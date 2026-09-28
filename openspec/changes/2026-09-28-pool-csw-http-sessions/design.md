## Context

`CSWClient` runs every OWSLib call through one funnel: `_run_in_executor(fn, *args, **kwargs)` →
`loop.run_in_executor(self._get_executor(), fn, *args, **kwargs)`, itself always reached via `_retry_async`. OWSLib
exposes no session/transport seam — `owslib/util.py`'s `http_post` / `http_get` / `openURL` call the module-level name
`requests` directly, so the only lever is that one name, `owslib.util.requests`. See proposal.md for the measurement.

`csw_client.py` is 998 lines against pylint's default `max-module-lines = 1000` — effectively no headroom. Any new logic
must live elsewhere; `xml_hardening.py` already establishes the pattern (a small, self-contained module installing a
scoped global patch, imported for its side effect).

## Goals / Non-Goals

**Goals:**

- Close the seam identified and measured in #19: pool one `requests.Session` per `CSWClient` worker thread.
- Change nothing about `csw_client.py`'s public behaviour or its line count budget.
- Give `CSWClient.__aexit__` an explicit, correct way to close exactly its own sessions, even when multiple `CSWClient`
  instances harvest concurrently (`orchestrator.py`'s `asyncio.gather` over repositories).

**Non-Goals:**

- See proposal.md.

## Decisions

1. **Thread-local `requests.Session`, not one shared Session** — `CSWClient` runs OWSLib on a bounded
   `ThreadPoolExecutor` (`csw_thread_pool_size`, default 4; `openspec/specs/csw-threadpool/`), and `requests.Session` is
   not documented thread-safe. One session per worker thread avoids any cross-thread sharing while still reusing the
   connection across that thread's sequential pages — which is where the handshake cost actually comes from (16
   sequential pages per harvest in the measured case).

2. **New `middleware/inspire/http_pooling.py`, not inline in `csw_client.py`** — Same reasoning as
   `openspec/specs/csw-xml-hardening/design.md` decision 2: `csw_client.py` has no line budget left, and bundling the
   patch, the registry and the shim in one small module makes the "installed after OWSLib's own import, wins regardless
   of import order" property a property of the module rather than of caller discipline. `csw_client.py`'s own changes
   are three lines: one import, `run_pooled(...)` replacing the direct `loop.run_in_executor(...)` call inside
   `_run_in_executor` (same line count — the call is longer, not an added line), and one `close_pooled(executor)` call
   in `_shutdown_executor`.

3. **Sessions tracked per owning executor, keyed by the executor object, not per-instance state on `CSWClient`** —
   `owslib.util.requests` is a single process-wide name; whatever object is bound there serves every concurrently
   running `CSWClient`. Rather than juggle per-instance monkeypatch swapping (races across concurrently harvesting
   repositories, since the last `CSWClient` to connect would clobber the attribute for all), the shim stays a single
   stable singleton, and the _registry_ that lets `close_pooled` find "my sessions" is keyed by `id(executor)`. This
   works because `ThreadPoolExecutor` worker threads are exclusive to the executor that created them for their whole
   life — so a session created on one CSWClient's worker thread is never touched by another CSWClient's
   `close_pooled(its_own_executor)` call. Verified by a test that runs two executors concurrently and asserts closing
   one does not touch the other's registered session. _Alternative considered:_ a `WeakKeyDictionary` keyed by executor,
   so an instance that skips `__aexit__` self-heals via GC — rejected as unnecessary complexity: `_shutdown_executor`
   already runs from both `__aexit__` and the existing `__del__` fallback (`openspec/specs/csw-threadpool/`), so every
   path that tears down the executor also calls `close_pooled` explicitly.

4. **Registration happens inside the executor call itself (`run_pooled`'s inner `call()`), not via a stored `CSWClient`
   attribute** — Avoids adding an `__init__` line to `csw_client.py` (see decision 2's line budget).
   `run_pooled(loop, executor, fn, *args, **kwargs)` wraps `fn` in a closure that first ensures + registers the calling
   thread's session, then runs `fn`. This is the same funnel every OWSLib call already goes through
   (`_run_in_executor`), so no call site needs to change beyond it.

5. **One connection per thread-local session (`pool_maxsize=1`)** — Each thread-local session only ever has one request
   in flight at a time; OWSLib's calls inside a worker thread are synchronous. A bigger pool would buy nothing.
   `csw_thread_pool_size` already bounds the number of worker threads, and therefore the number of open connections.

6. **`verify` / `cert` / `auth` are not touched** — OWSLib supplies them per call as kwargs sourced from
   `Authentication` (`http_post`/`http_get`/`http_prepare` in `owslib/util.py`), identical whether the session is pooled
   or ad hoc — `Session.post(url, ..., verify=..., cert=...)` accepts the same kwargs as
   `requests.post(url, ..., verify=..., cert=...)`. `openspec/specs/csw-ssl-verify/` behaviour is unaffected by
   construction, not by a compensating check.

7. **Rebinding `owslib.util.requests`, not the global `requests` module — see proposal.md's "Overturns" section** for
   why this is a deliberately narrower reach than the guidance it overturns.

8. **`close()` is best-effort (`contextlib.suppress(Exception)`)** — Mirrors `CSWClient.__del__`'s existing pattern. A
   session already broken by a connection error must not prevent shutdown from completing.

## Risks / Trade-offs

- **Process-wide reach of the monkeypatch.** Same shape of risk as `csw-xml-hardening`: anything else in the process
  that calls `owslib.util.http_post` / `http_get` / `openURL` now goes through the pooled shim too. Today nothing else
  in this codebase calls OWSLib directly outside `CSWClient`.
- **`ThreadPoolExecutor.shutdown(wait=False)` is non-blocking** (existing behaviour, unchanged by this proposal). In a
  cancellation scenario a worker thread could still be mid-request when `close_pooled` runs. `Session.close()` clears
  the adapter's idle-connection pool; a connection actively checked out for an in-flight request is not in that idle
  pool, so this is expected to be benign (worst case: one connection not returned to the OS-level pool promptly) rather
  than a race on live request state. Not a new risk class — `_shutdown_executor` already accepts this trade-off for the
  executor itself.
- **No live-network regression test.** Matching `csw-ssl-verify` and `csw-xml-hardening`, this ships without a test
  against a real CSW endpoint; the manual measurement in proposal.md/#19 is the evidence, and unit tests assert the
  mechanism (session identity reuse, per-executor isolation) rather than wall-clock.

## Migration Plan

None — no config field, no call-site changes beyond `csw_client.py`'s three-line delta. Existing YAML and deployments
are unaffected.
