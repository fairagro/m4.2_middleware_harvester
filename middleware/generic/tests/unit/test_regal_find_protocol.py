"""Unit tests for the generic Regal /find Protocol (offset-paginated JSON array)."""

from __future__ import annotations

import httpx
import pytest

from middleware.generic.config import Config, ProtocolType
from middleware.generic.errors import GenericProtocolError
from middleware.generic.plugin import GenericPlugin
from middleware.generic.protocol.json_array import JsonArrayProtocol
from middleware.generic.protocol.regal_find import RegalFindProtocol
from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.parsing.discovery import JsonLdDiscoveryResult

_FIND_URL = "https://frl.publisso.de/find"


def _config(url: str = _FIND_URL, page_size: int = 2) -> Config:
    return Config(
        protocol_type=ProtocolType.regal_find,
        sitemap_url=url,
        page_size=page_size,
        http=NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None),
    )


def _single_page_transport(page: list[object]) -> httpx.MockTransport:
    calls = {"n": 0}

    async def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=page if calls["n"] == 1 else [])

    return httpx.MockTransport(handler)


async def _discover(config: Config, transport: httpx.MockTransport) -> list[object]:
    async with NiceHttpClient(config.http, transport=transport) as client:
        return [result async for result in RegalFindProtocol(config, client).discover()]


@pytest.mark.asyncio
async def test_regal_find_protocol_resolves_from_registry_and_paginates() -> None:
    pages = {
        0: [{"@id": "frl:1", "title": ["One"]}, {"@id": "frl:2", "title": ["Two"]}],
        2: [{"@id": "frl:3", "title": ["Three"]}],
    }
    seen_queries: list[dict[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        query = dict(httpx.QueryParams(request.url.query))
        seen_queries.append(query)
        return httpx.Response(200, json=pages.get(int(query["from"]), []))

    async with NiceHttpClient(_config().http, transport=httpx.MockTransport(handler)) as client:
        protocol = GenericPlugin.create_protocol(_config(), client=client)
        assert isinstance(protocol, RegalFindProtocol)
        assert isinstance(protocol, JsonArrayProtocol)
        results = [result async for result in protocol.discover()]

    assert [r.identifier for r in results if isinstance(r, JsonLdDiscoveryResult)] == ["frl:1", "frl:2", "frl:3"]
    assert all(isinstance(r, JsonLdDiscoveryResult) and r.harvest_source_id is None for r in results)
    # Short second page stops pagination: no third request.
    assert len(seen_queries) == 2
    assert seen_queries[0] == {"q": "contentType:researchData", "format": "json", "from": "0", "until": "2"}
    assert seen_queries[1]["from"] == "2"


@pytest.mark.asyncio
async def test_regal_find_protocol_operator_query_wins_but_software_params_are_owned() -> None:
    seen: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.update(httpx.QueryParams(request.url.query))
        return httpx.Response(200, json=[])

    config = _config(f"{_FIND_URL}?q=otherType:x&sort=title&from=99&format=xml&until=1", page_size=5)
    _ = await _discover(config, httpx.MockTransport(handler))

    assert seen == {"q": "otherType:x", "sort": "title", "format": "json", "from": "0", "until": "1"}


@pytest.mark.asyncio
async def test_regal_find_protocol_uses_generic_config_default_page_size() -> None:
    seen_until: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_until.append(dict(httpx.QueryParams(request.url.query))["until"])
        return httpx.Response(200, json=[])

    config = Config(
        protocol_type=ProtocolType.regal_find,
        sitemap_url=_FIND_URL,
        http=NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None),
    )
    _ = await _discover(config, httpx.MockTransport(handler))

    assert seen_until == [str(config.page_size)]


@pytest.mark.asyncio
async def test_regal_find_protocol_reports_bad_elements_without_stopping() -> None:
    page: list[object] = [
        "not-an-object",
        {"doi": "10.4126/FRL01-only-doi"},
        {"@id": "frl:dup"},
        {"@id": "frl:dup"},
    ]
    results = await _discover(_config(page_size=10), _single_page_transport(page))

    assert isinstance(results[0], RecordProcessingError)
    assert results[0].record_id == "regal_find:from=0:index=0"
    assert "not an object" in str(results[0])
    assert isinstance(results[1], RecordProcessingError)
    assert results[1].record_id == "regal_find:from=0:index=1"
    assert "missing @id" in str(results[1])
    assert isinstance(results[2], JsonLdDiscoveryResult)
    assert results[2].identifier == "frl:dup"
    assert isinstance(results[3], SkippedRecord)


@pytest.mark.asyncio
async def test_regal_find_protocol_raises_on_non_array_payload() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"docs": []})

    with pytest.raises(GenericProtocolError, match="Regal /find response must be a JSON array"):
        _ = await _discover(_config(), httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_regal_find_protocol_expected_count_is_unknown() -> None:
    async with NiceHttpClient(_config().http) as client:
        assert await RegalFindProtocol(_config(), client).get_expected_count() is None
