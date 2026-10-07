"""Unit tests for the shared NiceHttpClient wrapper."""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from middleware.contracts.nice_http_client import (
    NiceHttpClient,
    NiceHttpClientConfig,
    RobotsTxtCache,
    RobotsTxtDisallowedError,
)

OK_STATUS = 200
EXPECTED_CALL_COUNT = 2


@pytest.mark.asyncio
async def test_ensure_allowed_raises_when_url_is_disallowed() -> None:
    config = NiceHttpClientConfig()
    client = NiceHttpClient(config)

    async with client:
        with (
            patch.object(NiceHttpClient, "is_allowed", AsyncMock(return_value=False)),
            pytest.raises(RobotsTxtDisallowedError, match="Dataset URL disallowed by robots.txt"),
        ):
            await client.ensure_allowed("https://example.com/dataset")


@pytest.mark.asyncio
async def test_ensure_allowed_allows_when_respect_robots_is_disabled() -> None:
    config = NiceHttpClientConfig(respect_robots_txt=False)
    client = NiceHttpClient(config)

    async with client:
        with patch.object(NiceHttpClient, "is_allowed", AsyncMock(side_effect=AssertionError("should not be called"))):
            await client.ensure_allowed("https://example.com/dataset")


@pytest.mark.asyncio
async def test_retry_get_retries_transient_status_codes() -> None:
    config = NiceHttpClientConfig(retry_attempts=1, max_retry_delay=0.1)
    client = NiceHttpClient(config)

    request = httpx.Request("GET", "https://example.com/test")
    response_503 = httpx.Response(503, request=request, headers={"Retry-After": "0"})
    response_200 = httpx.Response(200, request=request, content=b"ok")

    async with client:
        raw_client = client.client
        get_mock = AsyncMock(side_effect=[response_503, response_200])
        with patch.object(raw_client, "get", new=get_mock):
            response = await client.retry_get_with_client(raw_client, config, "https://example.com/test")

    assert response.status_code == OK_STATUS
    assert response.text == "ok"
    assert get_mock.call_count == EXPECTED_CALL_COUNT


@pytest.mark.asyncio
async def test_get_with_policy_applies_robots_and_rate_limit() -> None:
    config = NiceHttpClientConfig()
    client = NiceHttpClient(config)

    response_200 = httpx.Response(
        200,
        request=httpx.Request("GET", "https://example.com/test"),
        content=b"ok",
    )

    async with client:
        raw_client = client.client
        retry_get_mock = AsyncMock(return_value=response_200)
        with (
            patch.object(NiceHttpClient, "ensure_allowed", AsyncMock()) as ensure_allowed_mock,
            patch.object(NiceHttpClient, "wait_for_host", AsyncMock()) as wait_for_host_mock,
            patch.object(NiceHttpClient, "retry_get_with_client", retry_get_mock),
        ):
            response = await client.get_with_policy("https://example.com/test")

    assert response.status_code == OK_STATUS
    assert response.text == "ok"
    ensure_allowed_mock.assert_awaited_once_with("https://example.com/test")
    wait_for_host_mock.assert_awaited_once_with("https://example.com/test")
    retry_get_mock.assert_awaited_once_with(raw_client, config, "https://example.com/test", True)


def test_nice_http_client_uses_transport_and_headers() -> None:
    config = NiceHttpClientConfig(user_agent="CustomAgent/1.0", connect_timeout=1.0, read_timeout=2.0)

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["user-agent"] == "CustomAgent/1.0"
        return httpx.Response(200, text="ok")

    transport = httpx.MockTransport(handler)

    async def run() -> str:
        async with NiceHttpClient(config, transport=transport) as nice_http:
            response = await nice_http.client.get("https://example.org/")
            return response.text

    assert asyncio.run(run()) == "ok"


def test_max_requests_per_second_can_be_disabled() -> None:
    robots = RobotsTxtCache()
    called: list[float] = []

    async def fake_sleep(delay: float) -> None:
        called.append(delay)

    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr("middleware.contracts.nice_http_client.time.monotonic", lambda: 0.0)
        monkeypatch.setattr("middleware.contracts.nice_http_client.asyncio.sleep", fake_sleep)
        asyncio.run(robots.wait_for_host("example.org", None))
    finally:
        monkeypatch.undo()

    assert not called
    assert robots.host_last_request["example.org"] == 0.0


def test_sleep_for_host_respects_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    robots = RobotsTxtCache()
    monkeypatch.setattr("middleware.contracts.nice_http_client.time.monotonic", lambda: 0.0)
    slept: list[float] = []

    async def fake_sleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr("middleware.contracts.nice_http_client.asyncio.sleep", fake_sleep)

    asyncio.run(robots.wait_for_host("example.org", 2.0))
    assert slept == [0.5]
