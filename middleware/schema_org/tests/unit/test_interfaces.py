"""Unit tests for the Schema.org harvester interfaces."""

import asyncio

import httpx
import pytest
from rdflib import Graph

from middleware.schema_org.config import Config, DatasetType, PayloadType, SitemapType
from middleware.schema_org.dataset import UrlDiscoveryResult
from middleware.schema_org.errors import SchemaOrgDatasetError
from middleware.schema_org.html_jsonld_dataset import HtmlJsonLdDataset
from middleware.schema_org.plugin import create_mapper, create_sitemap
from middleware.schema_org.schema_org_mapper import DummySchemaOrgMapper
from middleware.schema_org.sitemap import XmlSitemap


def test_dummy_mapper_returns_jsonld() -> None:
    mapper = DummySchemaOrgMapper()
    result = mapper.map_graph(Graph())
    assert result.startswith("{") and "@context" in result


def test_create_sitemap_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
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
        dataset_type=DatasetType.html_jsonld,
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
            sitemap = XmlSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1", "https://example.org/dataset/2"]


def test_xml_sitemap_deduplicates_dataset_urls() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
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
            sitemap = XmlSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1"]


def test_xml_sitemap_prevents_sitemapindex_loops() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
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
            sitemap = XmlSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1"]


def test_create_mapper_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.dummy,
    )
    mapper = create_mapper(config)
    assert isinstance(mapper, DummySchemaOrgMapper)


# ---------------------------------------------------------------------------
# HtmlJsonLdDataset tests
# ---------------------------------------------------------------------------

SIMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "My Dataset",
    "identifier": "https://example.org/dataset/1"
  }
  </script>
</head>
<body></body>
</html>"""

MULTI_BLOCK_HTML = """<!DOCTYPE html>
<html>
<head>
  <script type="application/ld+json">
  {"@context": "https://schema.org", "@type": "Dataset", "name": "First"}
  </script>
  <script type="application/ld+json">
  {"@context": "https://schema.org", "@type": "Dataset", "name": "Second"}
  </script>
</head>
<body></body>
</html>"""

NO_JSONLD_HTML = """<!DOCTYPE html><html><head></head><body><p>No JSON-LD here.</p></body></html>"""

BAD_JSON_HTML = """<!DOCTYPE html>
<html><head>
  <script type="application/ld+json">not valid json{{{</script>
</head><body></body></html>"""


def test_html_jsonld_dataset_identifier() -> None:
    async def run() -> None:
        async with httpx.AsyncClient() as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client)
            assert ds.identifier == "https://example.org/page"

    asyncio.run(run())


def test_html_jsonld_dataset_to_graph_single_block() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SIMPLE_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        async with httpx.AsyncClient(transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client)
            graph = await ds.to_graph()
            return len(graph)

    triple_count = asyncio.run(run())
    assert triple_count > 0


def test_html_jsonld_dataset_to_graph_merges_multiple_blocks() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=MULTI_BLOCK_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        async with httpx.AsyncClient(transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client)
            graph = await ds.to_graph()
            return len(graph)

    triple_count = asyncio.run(run())
    assert triple_count > 0


def test_html_jsonld_dataset_raises_on_no_jsonld_blocks() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=NO_JSONLD_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client)
            await ds.to_graph()

    with pytest.raises(SchemaOrgDatasetError, match="No JSON-LD blocks"):
        asyncio.run(run())


def test_html_jsonld_dataset_raises_on_http_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client)
            await ds.to_graph()

    with pytest.raises(SchemaOrgDatasetError, match="HTTP 404"):
        asyncio.run(run())


def test_html_jsonld_dataset_raises_on_invalid_json() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=BAD_JSON_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client)
            await ds.to_graph()

    with pytest.raises(SchemaOrgDatasetError, match="Invalid JSON"):
        asyncio.run(run())
