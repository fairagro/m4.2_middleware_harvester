## Why

The CSW path opens a new TCP + TLS connection for every request. `CSWClient` reuses one `CatalogueServiceWeb` object for
the life of a harvest, but that object holds no session — OWSLib calls the **functional** `requests` API
(`owslib/util.py`: `http_post` → `requests.post`, `http_get`/`openURL` → `requests.get` / `requests.request`), which
internally opens and discards a connection on every call.

Measured against a real endpoint (`https://atlas.thuenen.de/catalogue/csw`, 151 records): 17 HTTP requests on 17
separate TCP connections, ~68–88 ms of connection setup per request, ~16% of harvest wall clock. `chunk_size` is not a
lever — this server (like many CSW deployments) caps the page size server-side regardless of what the client requests,
so the handshake count is fixed by the endpoint, not by our config. A prototype rebinding the one seam OWSLib exposes
measured **17 → 1 TCP connections, ~17% faster, identical record output** (151/151, 0 errors, at `chunk_size`
10/50/500).

Tracked as [#19](https://github.com/fairagro/m4.2_middleware_harvester/issues/19). @Zalfsten: "Currently this issue is
not really important. Proceed as you like as long as nothing breaks." — recorded on the issue 2026-09-22, the go-ahead
this proposal acts on.

## What Changes

- Add `middleware.inspire.http_pooling`, which rebinds the module-level name `owslib.util.requests` to a stand-in that
  forwards every call to a **thread-local pooled `requests.Session`** — one Session per `CSWClient` worker thread,
  reused across that thread's sequential CSW pages.
- Route every OWSLib call already funnelled through `CSWClient._run_in_executor` (all of them — `_connect`,
  `_iter_to_list`/paging, `get_record_count`) through this pooled dispatch, with zero change to call sites beyond
  `_run_in_executor` itself.
- Track pooled sessions per owning `ThreadPoolExecutor`, so `CSWClient.__aexit__` (via the existing
  `_shutdown_executor`) explicitly closes exactly its own sessions — never another, concurrently harvesting `CSWClient`
  instance's connections.
- Add `requests` as a direct dependency of `middleware/inspire` (previously transitive-only via `owslib`).

## Non-Goals

- Routing CSW through `NiceHttpClient`. The measurement does not justify reimplementing `getrecords2` on our own
  transport for a ~17% win; revisit only if rate-limiting/robots consistency with the Linked Data path is wanted for its
  own sake (`openspec/specs/async-concurrency/design.md` decision 1; `owslib.util.requests` remains the narrower,
  already-measured seam).
- Changing per-request TLS/auth behaviour. `verify` / `cert` / `auth` are still supplied by OWSLib on every call
  (sourced from `Authentication`, per `openspec/specs/csw-ssl-verify/`); pooling changes connection reuse only.
- Session pool sizing beyond one connection per worker thread. Each thread-local session only ever has one in-flight
  request (OWSLib calls are synchronous), so `pool_maxsize=1` is sufficient; `csw_thread_pool_size` already bounds
  worker-thread (and therefore session) count.
- The `_get_expected_datasets` / `run` double-client-lifecycle tidiness item from #19 (worth ~2 of 18 handshakes on its
  own) — separate, smaller follow-up if wanted.

## Overturns

`openspec/changes/archive/2026-08-11-inspire-csw-ssl-verify/design.md` decision 3 warns: "Do not patch `requests`
globals or set `PYTHONHTTPSVERIFY`." That warning was written against patching the **global** `requests` module. The
seam this change uses is narrower: the module-level name `owslib.util.requests` inside one third-party module. Rebinding
it leaves every other `requests` consumer in the process (arctrl, the OTLP exporter) on the stock functional API. There
is now a precedent for this kind of scoped, deliberate global mutation: `openspec/specs/csw-xml-hardening/design.md`
decision 4 accepted the same trade-off for the default XML parser.

## Capabilities

### New Capabilities

- `csw-http-pooling`: Thread-local pooled HTTP sessions for INSPIRE CSW / OWSLib connections.

### Modified Capabilities

- (none)

## Impact

- **Affected domains**: new `openspec/specs/csw-http-pooling/`; related pattern in `csw-ssl-verify` (how
  connection-level params are forwarded to OWSLib) and `csw-threadpool` (the executor whose worker threads own the
  pooled sessions).
- **Code**: new `middleware/inspire/src/middleware/inspire/http_pooling.py`; minimal changes to
  `middleware/inspire/src/middleware/inspire/csw_client.py` (`csw_client.py` is at pylint's `max-module-lines` ceiling —
  see design.md decision 2 for why the new logic lives in its own module); new unit tests under
  `middleware/inspire/tests/unit/`.
- **Config**: none — no new config field, no behaviour change for operators.
- **Dependencies**: `requests` added as a direct dependency of `middleware/inspire` (already resolved transitively via
  `owslib`; no version change).
- **Behaviour**: none intended for TLS/auth/retry semantics. Connection reuse only.
