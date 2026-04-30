"""Unit tests for the Schema.org harvester dummy interfaces."""

import asyncio

from rdflib import Graph

from middleware.schema_org.config import Config, DatasetType, PayloadType, SitemapType
from middleware.schema_org.interfaces import DummyDataset, DummySchemaOrgMapper, DummySitemap
from middleware.schema_org.plugin import create_mapper, create_sitemap


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
    assert isinstance(sitemap, DummySitemap)


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
