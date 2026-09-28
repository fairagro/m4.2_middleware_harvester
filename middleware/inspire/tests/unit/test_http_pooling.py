"""Regression tests for pooled OWSLib HTTP sessions.

These guard `openspec/specs/csw-http-pooling/`. The behaviour under test is connection
reuse, which is not directly observable without a real socket, so these assert the proxy
that provides it: the same `requests.Session` object is reused across repeated calls on
one worker thread, distinct threads never share a `Session`, and `close_pooled` closes
and forgets exactly the sessions registered for the executor it is given — not another,
concurrently harvesting client's sessions.
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import owslib.util  # type: ignore[import-untyped]
import pytest
import requests

from middleware.inspire import http_pooling
from middleware.inspire.http_pooling import _PooledOwslibRequests, close_pooled, install, run_pooled


def test_install_rebinds_owslib_requests_to_the_shim() -> None:
    assert isinstance(owslib.util.requests, _PooledOwslibRequests)


def test_install_is_idempotent() -> None:
    install()
    install()

    assert isinstance(owslib.util.requests, _PooledOwslibRequests)


def test_shim_methods_forward_to_the_thread_local_session() -> None:
    fake_session = MagicMock(spec=requests.Session)
    shim = _PooledOwslibRequests()

    with patch.object(http_pooling, "_ensure_thread_session", return_value=fake_session):
        shim.post("https://example.com", data="body", headers={"h": "v"}, verify=True)
        shim.get("https://example.com", verify=False)
        shim.request("POST", "https://example.com", cert=None)

    fake_session.post.assert_called_once_with("https://example.com", data="body", headers={"h": "v"}, verify=True)
    fake_session.get.assert_called_once_with("https://example.com", verify=False)
    fake_session.request.assert_called_once_with("POST", "https://example.com", cert=None)


@pytest.mark.asyncio
async def test_run_pooled_reuses_the_same_session_across_calls_on_one_thread() -> None:
    """One worker thread ⇒ one Session, reused across sequential pages (the connection-reuse win)."""
    seen: list[requests.Session] = []

    def record_session() -> None:
        seen.append(http_pooling._ensure_thread_session())

    with ThreadPoolExecutor(max_workers=1) as executor:
        loop = asyncio.get_running_loop()
        await run_pooled(loop, executor, record_session)
        await run_pooled(loop, executor, record_session)
        await run_pooled(loop, executor, record_session)

    assert len(seen) == 3  # noqa: PLR2004
    assert seen[0] is seen[1] is seen[2]


@pytest.mark.asyncio
async def test_run_pooled_gives_distinct_threads_distinct_sessions() -> None:
    sessions_by_thread: dict[int, requests.Session] = {}
    lock = threading.Lock()

    def record_session() -> None:
        with lock:
            sessions_by_thread[threading.get_ident()] = http_pooling._ensure_thread_session()

    with ThreadPoolExecutor(max_workers=4) as executor:
        loop = asyncio.get_running_loop()
        await asyncio.gather(*(run_pooled(loop, executor, record_session) for _ in range(8)))

    # However many distinct worker threads ran the eight calls, no two of them share a Session.
    assert len({id(session) for session in sessions_by_thread.values()}) == len(sessions_by_thread)


@pytest.mark.asyncio
async def test_close_pooled_closes_and_forgets_this_executors_sessions() -> None:
    with ThreadPoolExecutor(max_workers=1) as executor:
        loop = asyncio.get_running_loop()
        await run_pooled(loop, executor, http_pooling._ensure_thread_session)

    registered = http_pooling._sessions_by_executor[id(executor)]
    assert len(registered) == 1
    fake_session = MagicMock(spec=requests.Session)
    registered[0] = fake_session

    close_pooled(executor)

    fake_session.close.assert_called_once()
    assert id(executor) not in http_pooling._sessions_by_executor


def test_close_pooled_is_a_noop_for_an_unregistered_executor() -> None:
    """A CSWClient whose executor never ran any work must not error on shutdown."""
    close_pooled(ThreadPoolExecutor(max_workers=1))


@pytest.mark.asyncio
async def test_close_pooled_does_not_touch_another_executors_sessions() -> None:
    """Two concurrently harvesting CSWClient instances must not close each other's connections."""
    with ThreadPoolExecutor(max_workers=1) as executor_a, ThreadPoolExecutor(max_workers=1) as executor_b:
        loop = asyncio.get_running_loop()
        await run_pooled(loop, executor_a, http_pooling._ensure_thread_session)
        await run_pooled(loop, executor_b, http_pooling._ensure_thread_session)

        session_b = http_pooling._sessions_by_executor[id(executor_b)][0]
        fake_session_b = MagicMock(spec=requests.Session)
        http_pooling._sessions_by_executor[id(executor_b)][0] = fake_session_b

        close_pooled(executor_a)

        fake_session_b.close.assert_not_called()
        assert http_pooling._sessions_by_executor[id(executor_b)][0] is fake_session_b
        assert session_b is not None  # the original session object was simply left alone

    close_pooled(executor_b)
