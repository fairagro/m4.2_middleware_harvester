"""Unit tests for the Schema.org plugin entrypoint."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import RobotsTxtDisallowedError
from middleware.schema_org.config import (
    Config,
    DatasetType,
    NiceHttpClientConfig as SchemaOrgNiceHttpClientConfig,
    PayloadType,
    SitemapType,
)
from middleware.schema_org.dataset import UrlDiscoveryResult
from middleware.schema_org.plugin import SchemaOrgPlugin


class FakeSitemap:
    """A fake sitemap implementation for SchemaOrgPlugin tests."""

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


class FakeDataset:
    """A fake dataset implementation that successfully converts discovery results."""

    def __init__(self, url: str, _client: Any = None, _config: Any = None) -> None:
        """Initialize the fake dataset with its URL."""
        self._url = url

    @property
    def identifier(self) -> str:
        """Return the dataset identifier for the fake dataset."""
        return self._url

    @classmethod
    def from_discovery_result(
        cls,
        discovery_result: UrlDiscoveryResult,
        client: Any = None,
        config: Any = None,
    ) -> "FakeDataset":
        """Create a fake dataset from the discovery result."""
        del client, config
        return cls(discovery_result.url)

    async def to_graph(self) -> object:
        """Return a dummy graph payload for the fake dataset."""
        await asyncio.sleep(0)
        return f"graph:{self._url}"


@pytest.mark.asyncio
async def test_schema_org_plugin_run_maps_dataset_to_arc(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=SchemaOrgNiceHttpClientConfig(),
    )

    mock_mapper = MagicMock()
    mock_mapper.map_graph.return_value = "mapped:graph"

    def fake_create_sitemap(_config: Config, client: Any | None = None, **_kwargs: object) -> FakeSitemap:
        del client, _kwargs
        return FakeSitemap(["https://example.org/dataset/1"])

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr("middleware.schema_org.plugin.Dataset.registry", {DatasetType.html_jsonld: FakeDataset})
    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_mapper",
        staticmethod(lambda _config: mock_mapper),
    )
    monkeypatch.setattr("middleware.schema_org.plugin.NiceHttpClient.ensure_allowed", AsyncMock(return_value=None))

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert results == ["mapped:graph"]
    mock_mapper.map_graph.assert_called_once()
    assert isinstance(results[0], str)


@pytest.mark.asyncio
async def test_schema_org_plugin_run_yields_error_on_dataset_construction_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=SchemaOrgNiceHttpClientConfig(),
    )

    class BadDataset:
        @classmethod
        def from_discovery_result(
            cls,
            _discovery_result: UrlDiscoveryResult,
            client: Any = None,
            config: Any = None,
        ) -> "BadDataset":
            del client, config
            raise RuntimeError("bad dataset")

    def fake_create_sitemap(_config: Config, client: Any | None = None, **_kwargs: object) -> FakeSitemap:
        del client, _kwargs
        return FakeSitemap(["https://example.org/dataset/1"])

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr("middleware.schema_org.plugin.Dataset.registry", {DatasetType.html_jsonld: BadDataset})
    monkeypatch.setattr("middleware.schema_org.plugin.NiceHttpClient.ensure_allowed", AsyncMock(return_value=None))

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)


@pytest.mark.asyncio
async def test_schema_org_plugin_run_closes_cleanly_when_generator_is_cancelled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=SchemaOrgNiceHttpClientConfig(max_connections=2),
    )

    def fake_create_sitemap(_config: Config, client: Any | None = None, **_kwargs: object) -> FakeSitemap:
        del client, _kwargs
        return FakeSitemap(
            [
                "https://example.org/dataset/1",
                "https://example.org/dataset/2",
            ]
        )

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.Dataset.registry",
        {DatasetType.html_jsonld: FakeDataset},
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_mapper",
        staticmethod(lambda _config: MagicMock(map_graph=MagicMock(return_value="mapped:graph"))),
    )
    monkeypatch.setattr("middleware.schema_org.plugin.NiceHttpClient.ensure_allowed", AsyncMock(return_value=None))
    monkeypatch.setattr("middleware.schema_org.plugin.NiceHttpClient.wait_for_host", AsyncMock(return_value=None))

    loop = asyncio.get_running_loop()
    original_handler = loop.get_exception_handler()
    exceptions: list[BaseException | str] = []

    def handle_exception(_loop: asyncio.AbstractEventLoop, context: dict[str, object]) -> None:
        value = context.get("exception")
        if value is None:
            value = context.get("message", "unknown")
        if not isinstance(value, (BaseException, str)):
            value = str(value)
        exceptions.append(value)

    loop.set_exception_handler(handle_exception)

    try:
        agen = SchemaOrgPlugin(config).run()
        first_result = await agen.__anext__()
        assert first_result == "mapped:graph"
        await agen.aclose()
        await asyncio.sleep(0)
    finally:
        loop.set_exception_handler(original_handler)

    assert not exceptions


@pytest.mark.asyncio
async def test_schema_org_plugin_run_yields_error_when_robots_disallows_url(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=SchemaOrgNiceHttpClientConfig(),
    )

    def fake_create_sitemap(_config: Config, client: Any | None = None, **_kwargs: object) -> FakeSitemap:
        del client, _kwargs
        return FakeSitemap(["https://example.org/dataset/1"])

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.NiceHttpClient.ensure_allowed",
        AsyncMock(
            side_effect=RobotsTxtDisallowedError("Dataset URL disallowed by robots.txt: https://example.org/dataset/1")
        ),
    )

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)
