"""Integration tests for the EDAL-PGP plugin pipeline with recorded fixtures."""

import json
import os
from collections.abc import AsyncGenerator

import httpx
import pytest

from middleware.harvester.errors import HarvesterError
from middleware.schema_org.config import (
    Config,
    DatasetType,
    NiceHttpClientConfig as SchemaOrgNiceHttpClientConfig,
    PayloadType,
    SitemapType,
)
from middleware.schema_org.dataset import UrlDiscoveryResult
from middleware.schema_org.plugin import SchemaOrgPlugin

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")
EXPECTED_DATASETS = 2

_URLS = [
    "https://doi.org/10.5447/ipk/2011/0",
    "https://doi.org/10.5447/ipk/2016/0",
]


def _load_html(doi_slug: str) -> str:
    path = os.path.join(FIXTURE_DIR, f"edal_pgp_doi_{doi_slug}.html")
    with open(path) as f:
        return f.read()


class FakeSitemap:
    """A fake sitemap implementation for SchemaOrgPlugin integration tests."""

    def __init__(self, urls: list[str]) -> None:
        """Store the configured sitemap URLs."""
        self._urls = urls

    async def discover(self) -> AsyncGenerator[UrlDiscoveryResult, None]:
        """Yield configured discovery URLs from the fake sitemap."""
        for url in self._urls:
            yield UrlDiscoveryResult(url)

    async def get_expected_count(self) -> int | None:
        """Return the number of configured URLs."""
        return len(self._urls)


async def _mock_retry_get(self: object, url: str, **_kwargs: object) -> httpx.Response:
    del self
    if url == "https://doi.org/10.5447/ipk/2011/0":
        return httpx.Response(200, text=_load_html("2011_0"))
    if url == "https://doi.org/10.5447/ipk/2016/0":
        return httpx.Response(200, text=_load_html("2016_0"))
    msg = f"No fixture for URL: {url}"
    raise ValueError(msg)


def _fake_sitemap_factory(urls: list[str]) -> staticmethod:
    def create_sitemap(_config: object, **_kwargs: object) -> FakeSitemap:
        return FakeSitemap(urls)

    return staticmethod(create_sitemap)


@pytest.mark.asyncio
async def test_edal_pgp_plugin_pipeline_produces_valid_rocrate(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://doi.ipk-gatersleben.de/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.edal_pgp,
        http=SchemaOrgNiceHttpClientConfig(respect_robots_txt=False),
    )

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        _fake_sitemap_factory(_URLS),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.NiceHttpClient.retry_get",
        _mock_retry_get,
    )

    raw: list[str | HarvesterError] = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(raw) == EXPECTED_DATASETS
    results = [r for r in raw if isinstance(r, str)]
    assert len(results) == EXPECTED_DATASETS

    for i, result in enumerate(results):
        parsed = json.loads(result)
        assert "@context" in parsed
        assert "@graph" in parsed

    ro_2011 = json.loads(results[0])
    ro_2016 = json.loads(results[1])

    graph_2011 = ro_2011.get("@graph", [])
    graph_2016 = ro_2016.get("@graph", [])

    assert len(graph_2011) > 0
    assert len(graph_2016) > 0


@pytest.mark.asyncio
async def test_edal_pgp_2011_dot_0_license_placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://doi.ipk-gatersleben.de/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.edal_pgp,
        http=SchemaOrgNiceHttpClientConfig(respect_robots_txt=False),
    )

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        _fake_sitemap_factory(_URLS[:1]),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.NiceHttpClient.retry_get",
        _mock_retry_get,
    )

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(results) == 1
    result_str = results[0]
    assert isinstance(result_str, str)
    assert "URL not provided" in result_str


@pytest.mark.asyncio
async def test_edal_pgp_2011_dot_0_keywords_split(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://doi.ipk-gatersleben.de/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.edal_pgp,
        http=SchemaOrgNiceHttpClientConfig(respect_robots_txt=False),
    )

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        _fake_sitemap_factory(_URLS[:1]),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.NiceHttpClient.retry_get",
        _mock_retry_get,
    )

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(results) == 1
    result_str = results[0]
    assert isinstance(result_str, str)
    assert "bioinformatics" in result_str
    assert "database" in result_str
    assert "LIMS" in result_str


@pytest.mark.asyncio
async def test_edal_pgp_2016_dot_0_real_license(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://doi.ipk-gatersleben.de/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.edal_pgp,
        http=SchemaOrgNiceHttpClientConfig(respect_robots_txt=False),
    )

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        _fake_sitemap_factory(_URLS[1:]),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.NiceHttpClient.retry_get",
        _mock_retry_get,
    )

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(results) == 1
    result_str = results[0]
    assert isinstance(result_str, str)
    assert "creativecommons" in result_str
    assert "Klukas" in result_str
    assert "Pape" in result_str


@pytest.mark.asyncio
async def test_edal_pgp_both_datasets_produce_distinct_output(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://doi.ipk-gatersleben.de/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.edal_pgp,
        http=SchemaOrgNiceHttpClientConfig(respect_robots_txt=False),
    )

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        _fake_sitemap_factory(_URLS),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.NiceHttpClient.retry_get",
        _mock_retry_get,
    )

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(results) == EXPECTED_DATASETS
    assert isinstance(results[0], str)
    assert isinstance(results[1], str)
    assert results[0] != results[1]
