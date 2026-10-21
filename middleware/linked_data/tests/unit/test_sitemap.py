"""Linked Data sitemap unit tests."""

import asyncio

import httpx
import pytest

from middleware.contracts.errors import RecordProcessingError, SkippedRecord
from middleware.contracts.nice_http_client import NiceHttpClient
from middleware.linked_data.config import Config, DatasetType, NiceHttpClientConfig, SitemapType
from middleware.linked_data.dataset import UrlDiscoveryResult
from middleware.linked_data.errors import LinkedDataSitemapError
from middleware.linked_data.plugin import LinkedDataPlugin
from middleware.linked_data.sitemap import XmlSitemap

_TEST_HTTP = NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None)


def test_create_sitemap_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
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
