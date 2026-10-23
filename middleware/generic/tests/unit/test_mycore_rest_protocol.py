"""Unit tests for MycoreRestProtocol."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from middleware.contracts.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.mycore_rest import MycoreRestProtocol, MycoreRestProtocolConfig
from middleware.parsing.discovery import UrlDiscoveryResult

_TEST_HTTP = NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None)

_LIST_PAGE_1 = """<?xml version="1.0" encoding="UTF-8"?>
<mycoreobjects>
  <mycoreobject id="openagrar_mods_0001" lastModified="2026-01-01T00:00:00.000Z"/>
  <mycoreobject id="openagrar_mods_0002" lastModified="2026-01-02T00:00:00.000Z"/>
</mycoreobjects>
"""

_LIST_PAGE_2 = """<?xml version="1.0" encoding="UTF-8"?>
<mycoreobjects>
  <mycoreobject id="openagrar_mods_0003" lastModified="2026-01-03T00:00:00.000Z"/>
</mycoreobjects>
"""


def _config(entry_url: str, *, page_size: int = 2) -> MycoreRestProtocolConfig:
    return MycoreRestProtocolConfig(entry_url=entry_url, page_size=page_size)


def test_mycore_rest_protocol_paginates_with_after_id() -> None:
    config = _config("https://www.openagrar.de/api/v2/objects?category=state:published&type=mods", page_size=2)

    async def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        assert params.get("limit") == "2"
        assert "category" in params
        after_id = params.get("after_id")
        if after_id is None:
            return httpx.Response(200, content=_LIST_PAGE_1, headers={"X-Total-Count": "3"})
        assert after_id == "openagrar_mods_0002"
        return httpx.Response(200, content=_LIST_PAGE_2, headers={"X-Total-Count": "3"})

    transport = httpx.MockTransport(handler)

    async def run() -> list[object]:
        async with NiceHttpClient(_TEST_HTTP, transport=transport) as client:
            protocol = MycoreRestProtocol(config, client)
            return [item async for item in protocol.discover()]

    results = asyncio.run(run())
    urls = [item.url for item in results if isinstance(item, UrlDiscoveryResult)]
    assert urls == [
        "https://www.openagrar.de/api/v2/objects/openagrar_mods_0001",
        "https://www.openagrar.de/api/v2/objects/openagrar_mods_0002",
        "https://www.openagrar.de/api/v2/objects/openagrar_mods_0003",
    ]
    assert all(isinstance(item, UrlDiscoveryResult) and item.harvest_source_id for item in results)


def test_mycore_rest_protocol_get_expected_count() -> None:
    config = _config("https://example.org/api/v2/objects", page_size=10)

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_LIST_PAGE_1, headers={"X-Total-Count": "42"})

    transport = httpx.MockTransport(handler)

    async def run() -> int | None:
        async with NiceHttpClient(_TEST_HTTP, transport=transport) as client:
            protocol = MycoreRestProtocol(config, client)
            return await protocol.get_expected_count()

    assert asyncio.run(run()) == 42


def test_mycore_rest_protocol_fixture_list_path_derives_objects_base() -> None:
    config = _config("http://localhost:8080/api/v2/objects/list.xml", page_size=10)

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/list.xml")
        return httpx.Response(200, content=_LIST_PAGE_1)

    transport = httpx.MockTransport(handler)

    async def run() -> list[str]:
        async with NiceHttpClient(_TEST_HTTP, transport=transport) as client:
            protocol = MycoreRestProtocol(config, client)
            return [item.url async for item in protocol.discover() if isinstance(item, UrlDiscoveryResult)]

    assert asyncio.run(run()) == [
        "http://localhost:8080/api/v2/objects/openagrar_mods_0001",
        "http://localhost:8080/api/v2/objects/openagrar_mods_0002",
    ]


def test_mycore_rest_protocol_rejects_http_error() -> None:
    config = _config("https://example.org/api/v2/objects")

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, content=b"missing")

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with NiceHttpClient(_TEST_HTTP, transport=transport) as client:
            protocol = MycoreRestProtocol(config, client)
            await protocol.get_expected_count()

    with pytest.raises(GenericProtocolError, match="HTTP 404"):
        asyncio.run(run())
