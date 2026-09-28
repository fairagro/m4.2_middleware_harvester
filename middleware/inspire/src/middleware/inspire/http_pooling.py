"""Pooled HTTP sessions for OWSLib's functional `requests` API.

OWSLib's CSW client calls the module-level `requests` name bound in `owslib.util`
directly (`requests.post`, `requests.get`, `requests.request`) and exposes no
session or transport seam. Every call therefore opens and tears down its own
TCP+TLS connection — one handshake per CSW page, per DC-fallback page and per
`GetCapabilities` probe. Measured against a real endpoint: 17 connections for a
single 151-record harvest, ~17% of wall clock (see issue #19).

This module installs a stand-in at that one name, `owslib.util.requests`, so every
OWSLib call funnels through a pooled `requests.Session` instead. The stand-in is
scoped to `owslib.util.requests` — not the global `requests` module — so arctrl,
the OTLP exporter and anything else in the process that imports `requests`
directly are unaffected.

`verify` / `cert` / `auth` are still supplied by OWSLib on every call
(`owslib/util.py`: `http_post`, `http_get`, `openURL` all pass them as per-request
kwargs sourced from `Authentication`), exactly as they are with the unpooled
functional API. Pooling only changes connection reuse, not per-request semantics,
so `openspec/specs/csw-ssl-verify/` behaviour is unaffected.

One `requests.Session` per worker thread, not one shared `Session`, because
`CSWClient` runs OWSLib on a `ThreadPoolExecutor` and `requests.Session` is not
documented thread-safe. Sessions are tracked per owning executor — keyed by the
executor object, in a module-level registry — so a `CSWClient` can explicitly
close exactly its own sessions on `__aexit__` without disturbing another,
concurrently harvesting `CSWClient` instance's connections.

See `openspec/specs/csw-http-pooling/`.
"""

import asyncio
import contextlib
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import owslib.util  # type: ignore[import-untyped]
import requests
from requests.adapters import HTTPAdapter

_thread_local = threading.local()
_registry_lock = threading.Lock()
_sessions_by_executor: dict[int, list[requests.Session]] = {}


def _ensure_thread_session() -> requests.Session:
    """Return this thread's pooled Session, creating it (and a sized adapter) on first use."""
    session: requests.Session | None = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        # One connection is enough: a thread-local session only ever has one in-flight
        # request at a time (OWSLib calls are synchronous), so pooling buys reuse across
        # sequential pages, not concurrency within a thread.
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _thread_local.session = session
    return session


def _register(executor: ThreadPoolExecutor, session: requests.Session) -> None:
    """Record that `session` belongs to `executor`, so `close_pooled` can later close it."""
    with _registry_lock:
        sessions = _sessions_by_executor.setdefault(id(executor), [])
        if session not in sessions:
            sessions.append(session)


async def run_pooled[T](
    loop: asyncio.AbstractEventLoop,
    executor: ThreadPoolExecutor,
    fn: Callable[..., T],
    *args: object,
    **kwargs: object,
) -> T:
    """Run `fn(*args, **kwargs)` in `executor`, on a worker thread with a pooled HTTP session.

    Registers the calling worker thread's session under `executor` so `close_pooled` can
    later close exactly this executor's sessions.
    """

    def call() -> T:
        _register(executor, _ensure_thread_session())
        return fn(*args, **kwargs)

    return await loop.run_in_executor(executor, call)


def close_pooled(executor: ThreadPoolExecutor) -> None:
    """Close every pooled session registered for `executor` and forget them.

    Best-effort: a session already broken by a connection error is still discarded.
    """
    with _registry_lock:
        sessions = _sessions_by_executor.pop(id(executor), [])
    for session in sessions:
        with contextlib.suppress(Exception):
            session.close()


class _PooledOwslibRequests:
    """Stand-in for the `requests` module as seen by `owslib.util`.

    Forwards `.post` / `.get` / `.request` to the calling thread's pooled Session — the
    same call signature as the real functional `requests` API, since `Session.post` etc.
    accept the same positional/keyword arguments as `requests.post`.
    """

    @staticmethod
    def post(*args: object, **kwargs: object) -> requests.Response:
        return _ensure_thread_session().post(*args, **kwargs)  # type: ignore[arg-type]

    @staticmethod
    def get(*args: object, **kwargs: object) -> requests.Response:
        return _ensure_thread_session().get(*args, **kwargs)  # type: ignore[arg-type]

    @staticmethod
    def request(*args: object, **kwargs: object) -> requests.Response:
        return _ensure_thread_session().request(*args, **kwargs)  # type: ignore[arg-type]


def install() -> None:
    """Rebind `owslib.util.requests` to the pooled-session shim.

    Idempotent — safe to call more than once. Called once at import time, below.
    """
    owslib.util.requests = _PooledOwslibRequests()


install()
