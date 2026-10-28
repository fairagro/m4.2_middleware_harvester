"""Unit tests for the shared NiceHttpClient wrapper."""

import asyncio
import gzip
import zlib
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from middleware.contracts.nice_http_client import (
    NiceHttpClient,
    NiceHttpClientConfig,
    ResponseBodyTooLargeError,
    RobotsTxtCache,
    RobotsTxtDisallowedError,
)

OK_STATUS = 200
EXPECTED_CALL_COUNT = 2
SERVICE_UNAVAILABLE_STATUS = 503
DEFAULT_MAX_RESPONSE_BODY_BYTES = 33_554_432


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
    config = NiceHttpClientConfig(retry_attempts=1, max_retry_delay=0.1, respect_robots_txt=False)
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        del request
        call_count += 1
        if call_count == 1:
            return httpx.Response(503, headers={"Retry-After": "0"})
        return httpx.Response(200, content=b"ok")

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(config, transport=transport) as client:
        response = await client.retry_get("https://example.com/test")

    assert response.status_code == OK_STATUS
    assert response.text == "ok"
    assert call_count == EXPECTED_CALL_COUNT


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
        retry_get_mock = AsyncMock(return_value=response_200)
        with (
            patch.object(NiceHttpClient, "ensure_allowed", AsyncMock()) as ensure_allowed_mock,
            patch.object(NiceHttpClient, "wait_for_host", AsyncMock()) as wait_for_host_mock,
            patch.object(NiceHttpClient, "retry_get", retry_get_mock),
        ):
            response = await client.get_with_policy("https://example.com/test")

    assert response.status_code == OK_STATUS
    assert response.text == "ok"
    ensure_allowed_mock.assert_awaited_once_with("https://example.com/test")
    wait_for_host_mock.assert_awaited_once_with("https://example.com/test")
    retry_get_mock.assert_awaited_once_with(
        "https://example.com/test",
        follow_redirects=True,
        headers=None,
    )


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


def test_max_response_body_bytes_default_and_validation() -> None:
    assert NiceHttpClientConfig().max_response_body_bytes == DEFAULT_MAX_RESPONSE_BODY_BYTES
    assert NiceHttpClientConfig(max_response_body_bytes=1).max_response_body_bytes == 1
    with pytest.raises(ValueError):
        NiceHttpClientConfig(max_response_body_bytes=0)


@pytest.mark.asyncio
async def test_retry_get_rejects_oversized_content_length() -> None:
    config = NiceHttpClientConfig(max_response_body_bytes=10, retry_attempts=2, respect_robots_txt=False)
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        del request
        call_count += 1
        return httpx.Response(200, headers={"Content-Length": "100"}, content=b"x" * 100)

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(config, transport=transport) as client:
        with pytest.raises(ResponseBodyTooLargeError, match="Content-Length 100") as exc_info:
            await client.retry_get("https://example.com/big")

    assert exc_info.value.limit == 10
    assert exc_info.value.content_length == 100
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_get_rejects_oversized_streamed_body() -> None:
    config = NiceHttpClientConfig(max_response_body_bytes=10, retry_attempts=2, respect_robots_txt=False)
    call_count = 0

    async def app(
        scope: MutableMapping[str, Any],
        receive: Callable[[], Awaitable[MutableMapping[str, Any]]],
        send: Callable[[MutableMapping[str, Any]], Awaitable[None]],
    ) -> None:
        nonlocal call_count
        del receive
        assert scope["type"] == "http"
        call_count += 1
        # No Content-Length header: enforcement must count streamed bytes.
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"abcdefghij", "more_body": True})
        await send({"type": "http.response.body", "body": b"klmnopqrstuvwxyz", "more_body": False})

    transport = httpx.ASGITransport(app=app)
    async with NiceHttpClient(config, transport=transport) as client:
        with pytest.raises(ResponseBodyTooLargeError, match="read .* bytes") as exc_info:
            await client.retry_get("http://testserver/stream")

    assert exc_info.value.limit == 10
    assert exc_info.value.bytes_read is not None
    assert exc_info.value.bytes_read > 10
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_get_accepts_body_at_exact_limit() -> None:
    limit = 16
    body = b"a" * limit
    config = NiceHttpClientConfig(max_response_body_bytes=limit, respect_robots_txt=False)

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(config, transport=transport) as client:
        response = await client.retry_get("https://example.com/exact")

    assert response.status_code == OK_STATUS
    assert response.content == body


@pytest.mark.asyncio
async def test_response_body_too_large_is_not_retried() -> None:
    """Body-too-large must not be treated as a transient retryable failure."""
    config = NiceHttpClientConfig(max_response_body_bytes=5, retry_attempts=3, respect_robots_txt=False)
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        del request
        call_count += 1
        return httpx.Response(200, headers={"Content-Length": "999"}, content=b"x" * 999)

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(config, transport=transport) as client:
        with pytest.raises(ResponseBodyTooLargeError):
            await client.retry_get("https://example.com/once")

    assert call_count == 1
    assert issubclass(ResponseBodyTooLargeError, RuntimeError)


@pytest.mark.asyncio
async def test_retry_get_decodes_gzip_response_once() -> None:
    body = b"<urlset>plabipd</urlset>"
    config = NiceHttpClientConfig(respect_robots_txt=False)

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, headers={"Content-Encoding": "gzip"}, content=gzip.compress(body))

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(config, transport=transport) as client:
        response = await client.retry_get("https://example.com/sitemap.xml")

    assert response.status_code == OK_STATUS
    assert response.content == body


@pytest.mark.asyncio
async def test_retry_get_decodes_deflate_response_once() -> None:
    body = b"<urlset>plabipd</urlset>"
    config = NiceHttpClientConfig(respect_robots_txt=False)

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, headers={"Content-Encoding": "deflate"}, content=zlib.compress(body))

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(config, transport=transport) as client:
        response = await client.retry_get("https://example.com/sitemap.xml")

    assert response.status_code == OK_STATUS
    assert response.content == body


@pytest.mark.asyncio
async def test_retry_get_drops_encoding_and_length_headers_from_decoded_response() -> None:
    config = NiceHttpClientConfig(respect_robots_txt=False)

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, headers={"Content-Encoding": "gzip"}, content=gzip.compress(b"<urlset/>"))

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(config, transport=transport) as client:
        response = await client.retry_get("https://example.com/sitemap.xml")

    assert "content-encoding" not in response.headers
    assert "content-length" not in response.headers


@pytest.mark.asyncio
async def test_retry_get_rejects_gzip_body_over_limit_once_decoded() -> None:
    limit = 1_024
    compressed = gzip.compress(b"a" * (limit * 100))
    assert len(compressed) < limit
    config = NiceHttpClientConfig(max_response_body_bytes=limit, respect_robots_txt=False)

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, headers={"Content-Encoding": "gzip"}, content=compressed)

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(config, transport=transport) as client:
        with pytest.raises(ResponseBodyTooLargeError):
            await client.retry_get("https://example.com/bomb")


def _gzip_503(request: httpx.Request) -> httpx.Response:
    del request
    return httpx.Response(
        SERVICE_UNAVAILABLE_STATUS,
        headers={"Content-Encoding": "gzip", "Retry-After": "0"},
        content=gzip.compress(b"unavailable"),
    )


@pytest.mark.asyncio
async def test_gzip_503_returns_empty_body_without_encoding_headers() -> None:
    config = NiceHttpClientConfig(respect_robots_txt=False)

    async with NiceHttpClient(config, transport=httpx.MockTransport(_gzip_503)) as client:
        response = await client._get_with_body_limit("https://example.com/flaky")  # noqa: SLF001

    assert response.status_code == SERVICE_UNAVAILABLE_STATUS
    assert response.content == b""
    assert "content-encoding" not in response.headers
    assert "content-length" not in response.headers


@pytest.mark.asyncio
async def test_retry_get_retries_gzip_503() -> None:
    config = NiceHttpClientConfig(retry_attempts=1, max_retry_delay=0.1, respect_robots_txt=False)
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _gzip_503(request)
        return httpx.Response(200, content=b"ok")

    async with NiceHttpClient(config, transport=httpx.MockTransport(handler)) as client:
        response = await client.retry_get("https://example.com/flaky")

    assert response.text == "ok"
    assert call_count == EXPECTED_CALL_COUNT
