"""Unit tests for Regal /find sitemap discovery."""

from __future__ import annotations

import httpx
import pytest

from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType
from middleware.linked_data.dataset import JsonLdDiscoveryResult
from middleware.linked_data.plugin import LinkedDataPlugin
from middleware.linked_data.sitemap import RegalFindSitemap


def _config(
    url: str = "https://frl.publisso.de/find",
    page_size: int = 2,
) -> Config:
    return Config(
        sitemap_url=url,
        sitemap_type=SitemapType.regal_find,
        dataset_type=DatasetType.regal_jsonld,
        payload_type=PayloadType.regal_general,
        page_size=page_size,
        http=NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None),
    )


@pytest.mark.asyncio
async def test_regal_find_sitemap_paginates_and_yields_inline_payloads() -> None:
    pages = {
        0: [
            {"@id": "frl:1", "title": ["One"], "doi": "10.4126/FRL01-1"},
            {"@id": "frl:2", "title": ["Two"]},
        ],
        2: [
            {"@id": "frl:3", "title": ["Three"]},
        ],
    }
    seen_queries: list[dict[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        query = dict(httpx.QueryParams(request.url.query))
        seen_queries.append(query)
        offset = int(query.get("from", "0"))
        return httpx.Response(200, json=pages.get(offset, []))

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = LinkedDataPlugin.create_sitemap(_config(), client=client)
        assert isinstance(sitemap, RegalFindSitemap)
        results = [result async for result in sitemap.discover()]

    assert len(results) == 3
    assert all(isinstance(result, JsonLdDiscoveryResult) for result in results)
    assert [result.identifier for result in results] == ["frl:1", "frl:2", "frl:3"]  # type: ignore[union-attr]
    assert results[0].payload["title"] == ["One"]  # type: ignore[union-attr]
    assert seen_queries[0] == {
        "q": "contentType:researchData",
        "format": "json",
        "from": "0",
        "until": "2",
    }
    assert seen_queries[1]["from"] == "2"
    assert seen_queries[1]["until"] == "2"


@pytest.mark.asyncio
async def test_regal_find_sitemap_merges_operator_query_overrides() -> None:
    seen_query: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_query
        seen_query = dict(httpx.QueryParams(request.url.query))
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = RegalFindSitemap(
            _config("https://frl.publisso.de/find?q=otherType:x&sort=title&from=99&format=xml"),
            client,
        )
        _ = [result async for result in sitemap.discover()]

    assert seen_query["q"] == "otherType:x"
    assert seen_query["sort"] == "title"
    assert seen_query["format"] == "json"
    assert seen_query["from"] == "0"
    assert seen_query["until"] == "2"


@pytest.mark.asyncio
async def test_regal_find_sitemap_uses_config_default_page_size() -> None:
    seen_until: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_until.append(dict(httpx.QueryParams(request.url.query))["until"])
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    config = Config(
        sitemap_url="https://frl.publisso.de/find",
        sitemap_type=SitemapType.regal_find,
        dataset_type=DatasetType.regal_jsonld,
        payload_type=PayloadType.regal_general,
        http=NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None),
    )
    assert config.page_size == 200
    async with NiceHttpClient(config.http, transport=transport) as client:
        sitemap = RegalFindSitemap(config, client)
        _ = [result async for result in sitemap.discover()]

    assert seen_until == ["200"]


@pytest.mark.asyncio
async def test_regal_find_sitemap_url_until_overrides_page_size() -> None:
    seen_until: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_until.append(dict(httpx.QueryParams(request.url.query))["until"])
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = RegalFindSitemap(
            _config("https://frl.publisso.de/find?until=1", page_size=5),
            client,
        )
        _ = [result async for result in sitemap.discover()]

    assert seen_until == ["1"]


@pytest.mark.asyncio
async def test_regal_find_sitemap_yields_failure_for_records_without_at_id() -> None:
    calls = {"n": 0}

    async def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] > 1:
            return httpx.Response(200, json=[])
        return httpx.Response(
            200,
            json=[
                {"title": ["Missing identity"]},
                {"doi": "10.4126/FRL01-only-doi", "title": ["DOI only"]},
                {"@id": "frl:ok", "title": ["Ok"]},
            ],
        )

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = RegalFindSitemap(_config(), client)
        results = [result async for result in sitemap.discover()]

    assert len(results) == 3
    assert isinstance(results[0], RecordProcessingError)
    assert results[0].record_id == "regal_find:from=0:index=0"
    assert "missing @id" in str(results[0])
    assert isinstance(results[1], RecordProcessingError)
    assert results[1].record_id == "regal_find:from=0:index=1"
    assert isinstance(results[2], JsonLdDiscoveryResult)
    assert results[2].identifier == "frl:ok"


@pytest.mark.asyncio
async def test_regal_find_sitemap_yields_failure_for_non_object_array_elements() -> None:
    calls = {"n": 0}

    async def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] > 1:
            return httpx.Response(200, json=[])
        return httpx.Response(
            200,
            json=[
                "not-an-object",
                42,
                {"@id": "frl:ok", "title": ["Ok"]},
            ],
        )

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = RegalFindSitemap(_config(), client)
        results = [result async for result in sitemap.discover()]

    assert len(results) == 3
    assert isinstance(results[0], RecordProcessingError)
    assert results[0].record_id == "regal_find:from=0:index=0"
    assert "not an object" in str(results[0])
    assert "str" in str(results[0])
    assert isinstance(results[1], RecordProcessingError)
    assert results[1].record_id == "regal_find:from=0:index=1"
    assert "int" in str(results[1])
    assert isinstance(results[2], JsonLdDiscoveryResult)
    assert results[2].identifier == "frl:ok"


@pytest.mark.asyncio
async def test_regal_find_sitemap_raises_on_non_array_payload() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"docs": []})

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = RegalFindSitemap(_config(), client)
        from middleware.linked_data.errors import LinkedDataSitemapError

        with pytest.raises(LinkedDataSitemapError, match="JSON array"):
            _ = [result async for result in sitemap.discover()]


@pytest.mark.asyncio
async def test_regal_find_expected_count_is_unknown() -> None:
    async with NiceHttpClient(_config().http) as client:
        sitemap = RegalFindSitemap(_config(), client)
        assert await sitemap.get_expected_count() is None
