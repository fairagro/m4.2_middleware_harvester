"""Unit tests for MycoreSolrProtocol (generic entry point)."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from middleware.contracts.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.mycore_solr import MycoreSolrProtocol, MycoreSolrProtocolConfig
from middleware.parsing.discovery import UrlDiscoveryResult

_TEST_HTTP = NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None)


def _config(entry_url: str, *, page_size: int = 200) -> MycoreSolrProtocolConfig:
    return MycoreSolrProtocolConfig(entry_url=entry_url, page_size=page_size)


def test_mycore_solr_protocol_paginates_and_deduplicates() -> None:
    config = _config(
        "https://www.openagrar.de/servlets/solr/select?"
        "core=main&q=category.top%3A%22mir_genres%3Aresearch_data%22&rows=2&fl=id&wt=json"
    )
    first_page = {
        "response": {
            "numFound": 3,
            "start": 0,
            "docs": [{"id": "openagrar_mods_0001"}, {"id": "openagrar_mods_0002"}],
        }
    }
    second_page = {
        "response": {
            "numFound": 3,
            "start": 2,
            "docs": [{"id": "openagrar_mods_0002"}, {"id": "openagrar_mods_0003"}],
        }
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        start = int(dict(request.url.params).get("start", "0"))
        if start == 0:
            return httpx.Response(200, json=first_page)
        return httpx.Response(200, json=second_page)

    transport = httpx.MockTransport(handler)

    async def run() -> list[object]:
        async with NiceHttpClient(_TEST_HTTP, transport=transport) as client:
            protocol = MycoreSolrProtocol(config, client)
            return [item async for item in protocol.discover()]

    results = asyncio.run(run())
    urls = [item.url for item in results if isinstance(item, UrlDiscoveryResult)]
    assert urls == [
        "https://www.openagrar.de/receive/openagrar_mods_0001",
        "https://www.openagrar.de/receive/openagrar_mods_0002",
        "https://www.openagrar.de/receive/openagrar_mods_0003",
    ]


def test_mycore_solr_protocol_get_expected_count() -> None:
    config = _config("https://example.org/servlets/solr/select", page_size=10)

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"response": {"numFound": 42, "start": 0, "docs": [{"id": "a"}]}},
        )

    transport = httpx.MockTransport(handler)

    async def run() -> int | None:
        async with NiceHttpClient(_TEST_HTTP, transport=transport) as client:
            protocol = MycoreSolrProtocol(config, client)
            return await protocol.get_expected_count()

    assert asyncio.run(run()) == 42


def test_mycore_solr_protocol_rejects_non_object_payload() -> None:
    config = _config("https://example.org/servlets/solr/select")

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not", "an", "object"])

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with NiceHttpClient(_TEST_HTTP, transport=transport) as client:
            protocol = MycoreSolrProtocol(config, client)
            await protocol.get_expected_count()

    with pytest.raises(GenericProtocolError, match="JSON object"):
        asyncio.run(run())
