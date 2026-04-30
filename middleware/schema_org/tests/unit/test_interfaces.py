"""Unit tests for the Schema.org harvester dummy interfaces."""

import asyncio

import httpx
from rdflib import Graph

from middleware.schema_org.config import Config, DatasetType, PayloadType, SitemapType
from middleware.schema_org.interfaces import DummyDataset, DummySchemaOrgMapper, DummySitemap
from middleware.schema_org.plugin import create_mapper, create_sitemap
from middleware.schema_org.sitemap import XmlSitemap


def test_dummy_dataset_returns_graph() -> None:
    dataset = DummyDataset("urn:test")
    assert dataset.identifier == "urn:test"


def test_dummy_sitemap_discover_yields_nothing() -> None:
    config = Config(
        sitemap_urls=["https://example.org/sitemap.xml"],
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.dummy,
        payload_type=PayloadType.dummy,
    )
    sitemap = DummySitemap(config)
    results = asyncio.run(_collect_sitemap(sitemap))
    assert results == []


def test_dummy_mapper_returns_jsonld() -> None:
    mapper = DummySchemaOrgMapper()
    result = mapper.map_graph(Graph())
    assert result.startswith("{") and "@context" in result


def test_create_sitemap_from_config() -> None:
    config = Config(
        sitemap_urls=["https://example.org/sitemap.xml"],
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.dummy,
        payload_type=PayloadType.dummy,
    )
    sitemap = create_sitemap(config)
    assert isinstance(sitemap, XmlSitemap)


def test_xml_sitemap_discover_urlset() -> None:
    config = Config(
        sitemap_urls=["https://example.org/sitemap.xml"],
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
            sitemap = XmlSitemap(config, client=client)
            return [dataset.identifier async for dataset in sitemap.discover()]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1", "https://example.org/dataset/2"]


def test_create_mapper_from_config() -> None:
    config = Config(
        sitemap_urls=["https://example.org/sitemap.xml"],
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.dummy,
        payload_type=PayloadType.dummy,
    )
    mapper = create_mapper(config)
    assert isinstance(mapper, DummySchemaOrgMapper)


async def _collect_sitemap(sitemap: DummySitemap) -> list[object]:
    return [item async for item in sitemap.discover()]
