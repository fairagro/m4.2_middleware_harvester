"""Schema.org NiceHttpClient unit tests."""

import asyncio

import httpx
import pytest

from middleware.harvester.nice_http_client import NiceHttpClient, NiceHttpClientConfig, RobotsTxtCache


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
        monkeypatch.setattr("middleware.harvester.nice_http_client.time.monotonic", lambda: 0.0)
        monkeypatch.setattr("middleware.harvester.nice_http_client.asyncio.sleep", fake_sleep)
        asyncio.run(robots.wait_for_host("example.org", None))
    finally:
        monkeypatch.undo()

    assert not called
    assert robots.host_last_request["example.org"] == 0.0


def test_sleep_for_host_respects_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    robots = RobotsTxtCache()
    monkeypatch.setattr("middleware.harvester.nice_http_client.time.monotonic", lambda: 0.0)
    slept: list[float] = []

    async def fake_sleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr("middleware.harvester.nice_http_client.asyncio.sleep", fake_sleep)

    asyncio.run(robots.wait_for_host("example.org", 2.0))
    assert slept == [0.5]
