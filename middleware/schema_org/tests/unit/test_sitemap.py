"""Schema.org sitemap unit tests."""

import asyncio

import httpx
from test_fakes import UrlDiscoveryResult

from middleware.schema_org.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType
from middleware.schema_org.plugin import SchemaOrgPlugin
from middleware.schema_org.sitemap import MycoreSolrSitemap, XmlSitemap


def test_create_sitemap_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )

    async def create() -> None:
        timeout = httpx.Timeout(
            connect=config.http.connect_timeout, read=config.http.read_timeout, write=None, pool=None
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            sitemap = SchemaOrgPlugin.create_sitemap(config, client=client)
            assert isinstance(sitemap, XmlSitemap)

    asyncio.run(create())


def test_xml_sitemap_discover_urlset() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
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
        timeout = httpx.Timeout(
            connect=config.http.connect_timeout, read=config.http.read_timeout, write=None, pool=None
        )
        async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
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
        http=NiceHttpClientConfig(),
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
        timeout = httpx.Timeout(
            connect=config.http.connect_timeout, read=config.http.read_timeout, write=None, pool=None
        )
        async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
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
        http=NiceHttpClientConfig(),
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
        timeout = httpx.Timeout(
            connect=config.http.connect_timeout, read=config.http.read_timeout, write=None, pool=None
        )
        async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
            sitemap = XmlSitemap(config, client)
            return [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]

    results = asyncio.run(collect())
    assert results == ["https://example.org/dataset/1"]


def test_create_sitemap_from_config_mycore_solr() -> None:
    config = Config(
        sitemap_url="https://www.openagrar.de/servlets/solr/select?core=main&q=test&rows=1&fl=id&wt=json",
        sitemap_type=SitemapType.mycore_solr,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )

    async def create() -> None:
        timeout = httpx.Timeout(
            connect=config.http.connect_timeout, read=config.http.read_timeout, write=None, pool=None
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            sitemap = SchemaOrgPlugin.create_sitemap(config, client=client)
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
        http=NiceHttpClientConfig(),
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
        timeout = httpx.Timeout(
            connect=config.http.connect_timeout, read=config.http.read_timeout, write=None, pool=None
        )
        async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
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
        http=NiceHttpClientConfig(),
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
        timeout = httpx.Timeout(
            connect=config.http.connect_timeout, read=config.http.read_timeout, write=None, pool=None
        )
        async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
            sitemap = MycoreSolrSitemap(config, client)
            count = await sitemap.get_expected_count()
            urls = [result.url async for result in sitemap.discover() if isinstance(result, UrlDiscoveryResult)]
            return count, urls

    count, urls = asyncio.run(collect())

    assert count == 1
    assert urls == ["https://www.openagrar.de/receive/openagrar_mods_0001"]
