"""Unit tests for DCAT-AP catalog sitemap discovery (Hydra pagination)."""

from __future__ import annotations

import json

import httpx
import pytest
from rdflib import Namespace
from rdflib.namespace import DCTERMS

from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import Config, DatasetType, NiceHttpClientConfig, SitemapType
from middleware.linked_data.dataset.dcat_ap import DcatDatasetDiscoveryResult
from middleware.linked_data.errors import LinkedDataSitemapError
from middleware.linked_data.plugin import LinkedDataPlugin
from middleware.linked_data.sitemap import DcatApSitemap

_CATALOG_URL = "https://example.org/catalog.jsonld"
_FOAF = Namespace("http://xmlns.com/foaf/0.1/")

_PAGE_1: list[dict[str, object]] = [
    {
        "@id": f"{_CATALOG_URL}?page=1",
        "@type": ["http://www.w3.org/ns/hydra/core#PagedCollection"],
        "http://www.w3.org/ns/hydra/core#totalItems": [{"@value": 2}],
        "http://www.w3.org/ns/hydra/core#nextPage": [{"@value": f"{_CATALOG_URL}?page=2"}],
    },
    {
        "@id": "https://example.org/dataset/1",
        "@type": ["http://www.w3.org/ns/dcat#Dataset"],
        "http://purl.org/dc/terms/title": [{"@value": "Dataset One"}],
        "http://www.w3.org/ns/dcat#distribution": [{"@id": "https://example.org/dataset/1/resource/a"}],
        "http://purl.org/dc/terms/publisher": [{"@id": "https://example.org/organization/1"}],
    },
    {
        "@id": "https://example.org/dataset/1/resource/a",
        "@type": ["http://www.w3.org/ns/dcat#Distribution"],
        "http://purl.org/dc/terms/title": [{"@value": "File A"}],
        "http://www.w3.org/ns/dcat#accessURL": [{"@id": "https://example.org/files/a.csv"}],
    },
    {
        "@id": "https://example.org/organization/1",
        "@type": ["http://xmlns.com/foaf/0.1/Organization"],
        "http://xmlns.com/foaf/0.1/name": [{"@value": "Org One"}],
    },
]

_PAGE_2: list[dict[str, object]] = [
    {
        "@id": f"{_CATALOG_URL}?page=2",
        "@type": ["http://www.w3.org/ns/hydra/core#PagedCollection"],
        "http://www.w3.org/ns/hydra/core#totalItems": [{"@value": 2}],
    },
    {
        "@id": "https://example.org/dataset/2",
        "@type": ["http://www.w3.org/ns/dcat#Dataset"],
        "http://purl.org/dc/terms/title": [{"@value": "Dataset Two"}],
    },
]

_PAGES: dict[str, object] = {
    _CATALOG_URL: _PAGE_1,
    f"{_CATALOG_URL}?page=2": _PAGE_2,
}


def _config(url: str = _CATALOG_URL) -> Config:
    return Config(
        sitemap_url=url,
        sitemap_type=SitemapType.dcat_ap,
        dataset_type=DatasetType.dcat_ap,
        http=NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None),
    )


def _transport_for(pages: dict[str, object]) -> httpx.MockTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        key = str(request.url)
        body = pages.get(key)
        if body is None:
            return httpx.Response(404, text="not found")
        return httpx.Response(200, content=json.dumps(body), headers={"content-type": "application/ld+json"})

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_dcat_ap_sitemap_follows_hydra_pagination() -> None:
    transport = _transport_for(_PAGES)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = LinkedDataPlugin.create_sitemap(_config(), client=client)
        assert isinstance(sitemap, DcatApSitemap)
        results = [result async for result in sitemap.discover()]

    assert len(results) == 2
    assert all(isinstance(result, DcatDatasetDiscoveryResult) for result in results)
    assert [r.identifier for r in results] == [  # type: ignore[union-attr]
        "https://example.org/dataset/1",
        "https://example.org/dataset/2",
    ]


@pytest.mark.asyncio
async def test_dcat_ap_sitemap_extracts_distribution_and_publisher_into_subgraph() -> None:
    transport = _transport_for(_PAGES)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = DcatApSitemap(_config(), client)
        results = [result async for result in sitemap.discover()]

    first = results[0]
    assert isinstance(first, DcatDatasetDiscoveryResult)
    titles = {str(o) for o in first.graph.objects(None, DCTERMS.title)}
    assert titles == {"Dataset One", "File A"}
    names = {str(o) for o in first.graph.objects(None, _FOAF.name)}
    assert names == {"Org One"}

    second = results[1]
    assert isinstance(second, DcatDatasetDiscoveryResult)
    second_titles = {str(o) for o in second.graph.objects(None, DCTERMS.title)}
    assert second_titles == {"Dataset Two"}


@pytest.mark.asyncio
async def test_dcat_ap_sitemap_expected_count_reads_hydra_total_items() -> None:
    transport = _transport_for(_PAGES)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = DcatApSitemap(_config(), client)
        assert await sitemap.get_expected_count() == 2


@pytest.mark.asyncio
async def test_dcat_ap_sitemap_raises_on_pagination_loop() -> None:
    looping_page = [
        {
            "@id": f"{_CATALOG_URL}?page=loop",
            "@type": ["http://www.w3.org/ns/hydra/core#PagedCollection"],
            "http://www.w3.org/ns/hydra/core#nextPage": [{"@value": _CATALOG_URL}],
        },
    ]
    transport = _transport_for({_CATALOG_URL: looping_page})
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = DcatApSitemap(_config(), client)
        with pytest.raises(LinkedDataSitemapError, match="pagination loop"):
            _ = [result async for result in sitemap.discover()]


@pytest.mark.asyncio
async def test_dcat_ap_sitemap_raises_on_invalid_jsonld() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content="not json-ld at all {{{", headers={"content-type": "application/ld+json"})

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(_config().http, transport=transport) as client:
        sitemap = DcatApSitemap(_config(), client)
        with pytest.raises(LinkedDataSitemapError, match="Failed to fetch/parse"):
            _ = [result async for result in sitemap.discover()]
