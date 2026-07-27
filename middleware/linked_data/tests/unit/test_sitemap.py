"""Linked Data sitemap unit tests."""

import asyncio

import httpx
import pytest

from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType
from middleware.linked_data.dataset import UrlDiscoveryResult
from middleware.linked_data.errors import LinkedDataSitemapError
from middleware.linked_data.plugin import LinkedDataPlugin
from middleware.linked_data.sitemap import MycoreSolrSitemap, XmlSitemap

_TEST_HTTP = NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None)


def test_create_sitemap_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    async def create() -> None:
        async with NiceHttpClient(config.http) as client:
            sitemap = LinkedDataPlugin.create_sitemap(config, client=client)
            assert isinstance(sitemap, XmlSitemap)

    asyncio.run(create())


def test_xml_sitemap_discover_urlset() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    urlset = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.org/dataset/1</loc></url>
      <url><loc>https://example.org/dataset/2</loc></url>
    </urlset>
    """

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=urlset)

    transport = httpx.MockTransport(handler)

    async def collect() -> list[str]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = XmlSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1", "https://example.org/dataset/2"]


def test_xml_sitemap_yields_error_for_empty_loc_with_sitemap_url_in_record_id() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    urlset = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc></loc></url>
      <url><loc>https://example.org/dataset/1</loc></url>
    </urlset>
    """

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=urlset)

    transport = httpx.MockTransport(handler)

    async def collect() -> tuple[list[str], list[RecordProcessingError]]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = XmlSitemap(config, client)
            urls: list[str] = []
            errors: list[RecordProcessingError] = []
            async for result in sitemap.discover():
                if isinstance(result, UrlDiscoveryResult):
                    urls.append(result.url)
                elif isinstance(result, RecordProcessingError):
                    errors.append(result)
            return urls, errors

    urls, errors = asyncio.run(collect())
    assert urls == ["https://example.org/dataset/1"]
    assert len(errors) == 1
    assert errors[0].record_id == "xml_sitemap:https://example.org/sitemap.xml:index=0"


def test_xml_sitemap_yields_error_for_empty_loc_in_sitemapindex() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    root_index = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc></loc></sitemap>
      <sitemap><loc>https://example.org/child.xml</loc></sitemap>
    </sitemapindex>
    """

    child_urlset = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.org/dataset/1</loc></url>
    </urlset>
    """

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL("https://example.org/sitemap.xml"):
            return httpx.Response(200, text=root_index)
        if request.url == httpx.URL("https://example.org/child.xml"):
            return httpx.Response(200, text=child_urlset)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def collect() -> tuple[list[str], list[RecordProcessingError]]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = XmlSitemap(config, client)
            urls: list[str] = []
            errors: list[RecordProcessingError] = []
            async for result in sitemap.discover():
                if isinstance(result, UrlDiscoveryResult):
                    urls.append(result.url)
                elif isinstance(result, RecordProcessingError):
                    errors.append(result)
            return urls, errors

    urls, errors = asyncio.run(collect())
    assert urls == ["https://example.org/dataset/1"]
    assert len(errors) == 1
    assert errors[0].record_id == "xml_sitemap:https://example.org/sitemap.xml:index=0"


def test_xml_sitemap_raises_sitemap_error_on_malformed_xml() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<urlset><url><loc>broken")

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = XmlSitemap(config, client)
            async for _ in sitemap.discover():
                pass

    with pytest.raises(LinkedDataSitemapError, match="Failed to parse XML sitemap"):
        asyncio.run(run())


def test_xml_sitemap_raises_sitemap_error_on_unsupported_root() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>not a sitemap</body></html>")

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = XmlSitemap(config, client)
            async for _ in sitemap.discover():
                pass

    with pytest.raises(LinkedDataSitemapError, match="Unsupported sitemap root element"):
        asyncio.run(run())


def test_xml_sitemap_deduplicates_dataset_urls() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    urlset = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.org/dataset/1</loc></url>
      <url><loc>https://example.org/dataset/1</loc></url>
    </urlset>
    """

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=urlset)

    transport = httpx.MockTransport(handler)

    async def collect() -> tuple[list[str], list[SkippedRecord]]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = XmlSitemap(config, client)
            urls: list[str] = []
            skips: list[SkippedRecord] = []
            async for result in sitemap.discover():
                if isinstance(result, UrlDiscoveryResult):
                    urls.append(result.url)
                elif isinstance(result, SkippedRecord):
                    skips.append(result)
            return urls, skips

    urls, skips = asyncio.run(collect())
    assert urls == ["https://example.org/dataset/1"]
    assert len(skips) == 1
    assert skips[0].url == "https://example.org/dataset/1"


def test_xml_sitemap_prevents_sitemapindex_loops() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    root_index = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://example.org/sitemap.xml</loc></sitemap>
      <sitemap><loc>https://example.org/child.xml</loc></sitemap>
    </sitemapindex>
    """

    child_index = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://example.org/dataset-index.xml</loc></sitemap>
    </sitemapindex>
    """

    dataset_index = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.org/dataset/1</loc></url>
    </urlset>
    """

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL("https://example.org/sitemap.xml"):
            return httpx.Response(200, text=root_index)
        if request.url == httpx.URL("https://example.org/child.xml"):
            return httpx.Response(200, text=child_index)
        if request.url == httpx.URL("https://example.org/dataset-index.xml"):
            return httpx.Response(200, text=dataset_index)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def collect() -> list[str]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = XmlSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1"]


def test_create_sitemap_from_config_mycore_solr() -> None:
    config = Config(
        sitemap_url="https://www.openagrar.de/servlets/solr/select?core=main&q=test&rows=1&fl=id&wt=json",
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    async def create() -> None:
        async with NiceHttpClient(config.http) as client:
            sitemap = LinkedDataPlugin.create_sitemap(config, client=client)
            assert isinstance(sitemap, MycoreSolrSitemap)

    asyncio.run(create())


def test_mycore_solr_sitemap_paginates_and_deduplicates() -> None:
    config = Config(
        sitemap_url=(
            "https://www.openagrar.de/servlets/solr/select?"
            "core=main&q=category.top%3A%22mir_genres%3Aresearch_data%22&rows=2&fl=id&wt=json"
        ),
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
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
    second_page_start = 2

    async def handler(request: httpx.Request) -> httpx.Response:
        query = dict(request.url.params)
        start = int(query.get("start", "0"))
        if start == 0:
            return httpx.Response(200, json=first_page)
        if start == second_page_start:
            return httpx.Response(200, json=second_page)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def collect() -> list[str]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = MycoreSolrSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == [
        "https://www.openagrar.de/receive/openagrar_mods_0001",
        "https://www.openagrar.de/receive/openagrar_mods_0002",
        "https://www.openagrar.de/receive/openagrar_mods_0003",
    ]


def test_mycore_solr_sitemap_fills_defaults_for_query_free_url() -> None:
    config = Config(
        sitemap_url="https://www.openagrar.de/servlets/solr/select",
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        page_size=7,
        http=_TEST_HTTP,
    )
    seen_query: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_query
        seen_query = dict(request.url.params)
        return httpx.Response(
            200,
            json={
                "response": {
                    "numFound": 1,
                    "start": 0,
                    "docs": [{"id": "openagrar_mods_0001"}],
                }
            },
        )

    transport = httpx.MockTransport(handler)

    async def collect() -> list[str]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = MycoreSolrSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://www.openagrar.de/receive/openagrar_mods_0001"]
    assert seen_query == {
        "core": "main",
        "q": "*:*",
        "fl": "id",
        "wt": "json",
        "rows": "7",
        "start": "0",
    }


def test_mycore_solr_sitemap_operator_params_override_defaults() -> None:
    config = Config(
        sitemap_url=(
            "https://www.openagrar.de/servlets/solr/select?"
            "q=category.top%3A%22mir_genres%3Aresearch_data%22&fq=state%3Apublished"
        ),
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        page_size=4,
        http=_TEST_HTTP,
    )
    seen_query: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_query
        seen_query = dict(request.url.params)
        return httpx.Response(
            200,
            json={
                "response": {
                    "numFound": 1,
                    "start": 0,
                    "docs": [{"id": "openagrar_mods_0001"}],
                }
            },
        )

    transport = httpx.MockTransport(handler)

    async def collect() -> list[str]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = MycoreSolrSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://www.openagrar.de/receive/openagrar_mods_0001"]
    assert seen_query["q"] == 'category.top:"mir_genres:research_data"'
    assert seen_query["fq"] == "state:published"
    assert seen_query["core"] == "main"
    assert seen_query["fl"] == "id"
    assert seen_query["wt"] == "json"
    assert seen_query["rows"] == "4"
    assert seen_query["start"] == "0"


def test_mycore_solr_sitemap_ignores_operator_wt() -> None:
    config = Config(
        sitemap_url="https://www.openagrar.de/servlets/solr/select?wt=xml&q=test",
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        page_size=2,
        http=_TEST_HTTP,
    )
    seen_query: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_query
        seen_query = dict(request.url.params)
        return httpx.Response(
            200,
            json={
                "response": {
                    "numFound": 1,
                    "start": 0,
                    "docs": [{"id": "openagrar_mods_0001"}],
                }
            },
        )

    transport = httpx.MockTransport(handler)

    async def collect() -> list[str]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = MycoreSolrSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://www.openagrar.de/receive/openagrar_mods_0001"]
    assert seen_query["wt"] == "json"
    assert seen_query["q"] == "test"


def test_mycore_solr_sitemap_url_rows_overrides_page_size() -> None:
    config = Config(
        sitemap_url=("https://www.openagrar.de/servlets/solr/select?core=main&q=test&rows=2&fl=id&wt=json"),
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        page_size=50,
        http=_TEST_HTTP,
    )
    seen_rows: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        query = dict(request.url.params)
        seen_rows.append(query["rows"])
        start = int(query.get("start", "0"))
        if start == 0:
            return httpx.Response(
                200,
                json={
                    "response": {
                        "numFound": 1,
                        "start": 0,
                        "docs": [{"id": "openagrar_mods_0001"}],
                    }
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def collect() -> list[str]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = MycoreSolrSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://www.openagrar.de/receive/openagrar_mods_0001"]
    assert seen_rows == ["2"]


def test_mycore_solr_sitemap_uses_page_size_when_rows_absent() -> None:
    config = Config(
        sitemap_url=("https://www.openagrar.de/servlets/solr/select?core=main&q=test&fl=id&wt=json"),
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        page_size=3,
        http=_TEST_HTTP,
    )
    seen_rows: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        query = dict(request.url.params)
        seen_rows.append(query["rows"])
        start = int(query.get("start", "0"))
        if start == 0:
            return httpx.Response(
                200,
                json={
                    "response": {
                        "numFound": 1,
                        "start": 0,
                        "docs": [{"id": "openagrar_mods_0001"}],
                    }
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def collect() -> list[str]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = MycoreSolrSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://www.openagrar.de/receive/openagrar_mods_0001"]
    assert seen_rows == ["3"]


def test_mycore_solr_sitemap_get_expected_count_uses_cached_first_page() -> None:
    config = Config(
        sitemap_url=("https://www.openagrar.de/servlets/solr/select?core=main&q=test&rows=1&fl=id&wt=json"),
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    response = {
        "response": {
            "numFound": 1,
            "start": 0,
            "docs": [{"id": "openagrar_mods_0001"}],
        }
    }

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response)

    transport = httpx.MockTransport(handler)

    async def collect() -> tuple[int | None, list[str]]:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = MycoreSolrSitemap(config, client)
            count = await sitemap.get_expected_count()
            urls = [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]
            return count, urls

    count, urls = asyncio.run(collect())

    assert count == 1
    assert urls == ["https://www.openagrar.de/receive/openagrar_mods_0001"]


def test_mycore_solr_sitemap_raises_on_non_object_payload() -> None:
    config = Config(
        sitemap_url="https://www.openagrar.de/servlets/solr/select",
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=_TEST_HTTP,
    )

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not", "an", "object"])

    transport = httpx.MockTransport(handler)

    async def collect() -> None:
        async with NiceHttpClient(config.http, transport=transport) as client:
            sitemap = MycoreSolrSitemap(config, client)
            _ = [result async for result in sitemap.discover()]

    with pytest.raises(LinkedDataSitemapError, match="JSON object"):
        asyncio.run(collect())
