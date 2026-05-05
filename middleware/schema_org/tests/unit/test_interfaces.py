"""Unit tests for the Schema.org harvester interfaces."""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.harvester.errors import RecordProcessingError
from middleware.schema_org.config import Config, DatasetType, PayloadType, SitemapType
from middleware.schema_org.dataset import DiscoveryResult, UrlDiscoveryResult
from middleware.schema_org.dataset.html_jsonld import HtmlJsonLdDataset
from middleware.schema_org.errors import SchemaOrgDatasetError, SchemaOrgError
from middleware.schema_org.plugin import create_mapper, create_sitemap, get_expected_datasets, run_plugin
from middleware.schema_org.schema_org_mapper import GeneralSchemaOrgMapper
from middleware.schema_org.sitemap import MycoreSolrSitemap, XmlSitemap


class FakeSitemap:
    """A lightweight fake sitemap for unit tests."""

    def __init__(self, urls: list[str]) -> None:
        """Store the configured sitemap URLs."""
        self._urls = urls

    async def discover(self) -> AsyncGenerator[UrlDiscoveryResult, None]:
        """Yield the configured discovery URLs."""
        for url in self._urls:
            yield UrlDiscoveryResult(url)

    async def get_expected_count(self) -> int | None:
        """Return the number of URLs in the fake sitemap."""
        return len(self._urls)


class BadFakeDataset:
    """A dataset implementation that fails during discovery conversion."""

    def __init__(self, url: str, _client: httpx.AsyncClient | None = None, _config: Config | None = None) -> None:
        """Create a failing fake dataset instance."""
        self._url = url

    @property
    def identifier(self) -> str:
        """Return the dataset identifier for the fake dataset."""
        return self._url

    @classmethod
    def from_discovery_result(
        cls,
        _discovery_result: DiscoveryResult,
        client: httpx.AsyncClient | None = None,
        config: Config | None = None,
    ) -> "BadFakeDataset":
        """Raise a SchemaOrgError to simulate dataset construction failure."""
        if client is not None or config is not None:
            del client, config
        raise SchemaOrgError("bad dataset")

    async def to_graph(self) -> object:
        """Return a dummy graph payload for the bad fake dataset."""
        await asyncio.sleep(0)
        return f"graph:{self._url}"


class GoodFakeDataset:
    """A dataset implementation that successfully converts discovery results."""

    def __init__(self, url: str, _client: httpx.AsyncClient | None = None, _config: Config | None = None) -> None:
        """Create a successful fake dataset instance."""
        self._url = url

    @property
    def identifier(self) -> str:
        """Return the dataset identifier for the good fake dataset."""
        return self._url

    @classmethod
    def from_discovery_result(
        cls,
        discovery_result: UrlDiscoveryResult,
        client: httpx.AsyncClient | None = None,
        config: Config | None = None,
    ) -> "GoodFakeDataset":
        """Construct a successful fake dataset from a discovery result."""
        if client is not None or config is not None:
            del client, config
        return cls(discovery_result.url)

    async def to_graph(self) -> object:
        """Return a dummy graph payload for the good fake dataset."""
        await asyncio.sleep(0)
        return f"graph:{self._url}"


def test_general_mapper_returns_jsonld() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))

    mapper = GeneralSchemaOrgMapper()
    result = mapper.map_graph(graph)

    assert result.startswith("{") and "@context" in result


def test_create_sitemap_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
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
        payload_type=PayloadType.general,
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
        payload_type=PayloadType.general,
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
        payload_type=PayloadType.general,
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
        payload_type=PayloadType.general,
    )
    mapper = create_mapper(config)
    assert isinstance(mapper, GeneralSchemaOrgMapper)


def test_create_sitemap_from_config_mycore_solr() -> None:
    config = Config(
        sitemap_url="https://www.openagrar.de/servlets/solr/select?core=main&q=test&rows=1&fl=id&wt=json",
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
    )

    async def create() -> None:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            sitemap = create_sitemap(config, client=client)
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
        payload_type=PayloadType.general,
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
        async with httpx.AsyncClient(transport=transport, timeout=config.timeout) as client:
            sitemap = MycoreSolrSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == [
        "https://www.openagrar.de/receive/openagrar_mods_0001",
        "https://www.openagrar.de/receive/openagrar_mods_0002",
        "https://www.openagrar.de/receive/openagrar_mods_0003",
    ]


def test_mycore_solr_sitemap_get_expected_count_uses_cached_first_page() -> None:
    config = Config(
        sitemap_url=("https://www.openagrar.de/servlets/solr/select?core=main&q=test&rows=1&fl=id&wt=json"),
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
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
        async with httpx.AsyncClient(transport=transport, timeout=config.timeout) as client:
            sitemap = MycoreSolrSitemap(config, client)
            count = await sitemap.get_expected_count()
            urls = [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]
            return count, urls

    count, urls = asyncio.run(collect())

    assert count == 1
    assert urls == ["https://www.openagrar.de/receive/openagrar_mods_0001"]


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


def test_html_jsonld_dataset_invalid_json_error_includes_block() -> None:
    invalid_block = '{"@context": "https://schema.org", "@type": "Dataset", invalid}'
    html = f"""<!DOCTYPE html>
<html>
<head>
  <script type="application/ld+json">
  {invalid_block}
  </script>
</head>
<body></body>
</html>"""

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with httpx.AsyncClient(transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client)
            await ds.to_graph()

    with pytest.raises(SchemaOrgDatasetError) as exc_info:
        asyncio.run(run())

    assert invalid_block in str(exc_info.value)


def test_html_jsonld_dataset_follows_redirects() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL("https://doi.org/10.5447/ipk/2024/11"):
            return httpx.Response(302, headers={"location": "https://doi.ipk-gatersleben.de/actual"})
        if request.url == httpx.URL("https://doi.ipk-gatersleben.de/actual"):
            return httpx.Response(200, text=SIMPLE_HTML, headers={"content-type": "text/html"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        async with httpx.AsyncClient(transport=transport, follow_redirects=True) as client:
            ds = HtmlJsonLdDataset("https://doi.org/10.5447/ipk/2024/11", client)
            graph = await ds.to_graph()
            return len(graph)

    triple_count = asyncio.run(run())
    assert triple_count > 0


@pytest.mark.asyncio
async def test_html_jsonld_dataset_offloads_large_jsonld_to_thread() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SIMPLE_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        async with httpx.AsyncClient(transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, jsonld_parse_threshold_bytes=0)
            with patch(
                "middleware.schema_org.dataset.html_jsonld.asyncio.to_thread",
                new=AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)),
            ) as to_thread_mock:
                graph = await ds.to_graph()
                assert to_thread_mock.called
                return len(graph)

    assert await run() > 0


@pytest.mark.asyncio
async def test_schema_org_plugin_get_expected_datasets_returns_none_on_failure() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
    )

    class FakeSitemap:
        def __init__(self, config: Config, client: httpx.AsyncClient) -> None:
            pass

        async def get_expected_count(self) -> int | None:
            raise RuntimeError("failed")

    def fake_create_sitemap(_config: Config, client: httpx.AsyncClient) -> FakeSitemap:
        return FakeSitemap(_config, client)

    with patch("middleware.schema_org.plugin.create_sitemap", fake_create_sitemap):
        result = await get_expected_datasets(config)

    assert result is None


@pytest.mark.asyncio
async def test_schema_org_plugin_get_expected_datasets_returns_count() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
    )

    class FakeSitemap:
        def __init__(self, config: Config, client: httpx.AsyncClient) -> None:
            pass

        async def get_expected_count(self) -> int | None:
            return 5

    def fake_create_sitemap(_config: Config, client: httpx.AsyncClient) -> FakeSitemap:
        return FakeSitemap(_config, client)

    expected_count = 5
    with patch("middleware.schema_org.plugin.create_sitemap", fake_create_sitemap):
        result = await get_expected_datasets(config)

    assert result == expected_count


@pytest.mark.asyncio
async def test_schema_org_plugin_run_plugin_returns_record_processing_error_for_bad_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
    )

    def fake_create_sitemap(_config: Config, **_kwargs: object) -> FakeSitemap:
        return FakeSitemap(["https://example.org/dataset/fast"])

    mock_mapper = MagicMock()
    mock_mapper.map_graph.side_effect = lambda graph: f"mapped:{graph}"

    monkeypatch.setattr("middleware.schema_org.plugin.create_sitemap", fake_create_sitemap)
    monkeypatch.setattr("middleware.schema_org.plugin.Dataset.registry", {DatasetType.html_jsonld: BadFakeDataset})
    monkeypatch.setattr("middleware.schema_org.plugin.create_mapper", lambda _: mock_mapper)

    results = [item async for item in run_plugin(config)]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)


@pytest.mark.asyncio
async def test_schema_org_plugin_run_plugin_maps_valid_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
    )

    def fake_create_sitemap(_config: Config, **_kwargs: object) -> FakeSitemap:
        return FakeSitemap(["https://example.org/dataset/slow"])

    mock_mapper = MagicMock()
    mock_mapper.map_graph.side_effect = lambda graph: f"mapped:{graph}"

    monkeypatch.setattr("middleware.schema_org.plugin.create_sitemap", fake_create_sitemap)
    monkeypatch.setattr("middleware.schema_org.plugin.Dataset.registry", {DatasetType.html_jsonld: GoodFakeDataset})
    monkeypatch.setattr("middleware.schema_org.plugin.create_mapper", lambda _: mock_mapper)

    results = [item async for item in run_plugin(config)]

    assert results == ["mapped:graph:https://example.org/dataset/slow"]
