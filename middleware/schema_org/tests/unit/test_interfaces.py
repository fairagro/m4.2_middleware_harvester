"""Unit tests for the Schema.org harvester dummy interfaces."""

import asyncio

import httpx
from rdflib import Graph

from middleware.schema_org.config import Config, DatasetType, PayloadType, SitemapType
from middleware.schema_org.dataset import DummyDataset
from middleware.schema_org.plugin import create_mapper, create_sitemap
from middleware.schema_org.schema_org_mapper import DummySchemaOrgMapper
from middleware.schema_org.sitemap import XmlSitemap


def test_dummy_dataset_returns_graph() -> None:
    dataset = DummyDataset("urn:test")
    assert dataset.identifier == "urn:test"


def test_dummy_mapper_returns_jsonld() -> None:
    mapper = DummySchemaOrgMapper()
    result = mapper.map_graph(Graph())
    assert result.startswith("{") and "@context" in result


def test_create_sitemap_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.dummy,
        payload_type=PayloadType.dummy,
    )

    async def create() -> None:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            sitemap = create_sitemap(config, client=client)
            assert isinstance(sitemap, XmlSitemap)

    asyncio.run(create())


def test_xml_sitemap_discover_urlset() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.dummy,
        payload_type=PayloadType.dummy,
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
        async with httpx.AsyncClient(transport=transport, timeout=config.timeout) as client:
            sitemap = XmlSitemap(config, client, DummyDataset)
            return [dataset.identifier async for dataset in sitemap.discover()]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1", "https://example.org/dataset/2"]


def test_xml_sitemap_deduplicates_dataset_urls() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.dummy,
        payload_type=PayloadType.dummy,
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

    async def collect() -> list[str]:
        async with httpx.AsyncClient(transport=transport, timeout=config.timeout) as client:
            sitemap = XmlSitemap(config, client, DummyDataset)
            return [dataset.identifier async for dataset in sitemap.discover()]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1"]


def test_xml_sitemap_prevents_sitemapindex_loops() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.dummy,
        payload_type=PayloadType.dummy,
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
        async with httpx.AsyncClient(transport=transport, timeout=config.timeout) as client:
            sitemap = XmlSitemap(config, client, DummyDataset)
            return [dataset.identifier async for dataset in sitemap.discover()]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1"]


def test_create_mapper_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.dummy,
        payload_type=PayloadType.dummy,
    )
    mapper = create_mapper(config)
    assert isinstance(mapper, DummySchemaOrgMapper)
