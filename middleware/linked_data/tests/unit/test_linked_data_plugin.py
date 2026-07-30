"""Unit tests for the Linked Data plugin entrypoint."""

import asyncio
from collections.abc import AsyncGenerator, Mapping
from unittest.mock import AsyncMock, MagicMock

import pytest
from rdflib import Graph

from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient, RobotsTxtDisallowedError
from middleware.harvester.plugin_base import HarvestedArc
from middleware.linked_data.config import (
    Config,
    DatasetType,
    NiceHttpClientConfig as LinkedDataNiceHttpClientConfig,
    PayloadType,
    SitemapType,
)
from middleware.linked_data.dataset import UrlDiscoveryResult
from middleware.linked_data.errors import LinkedDataSitemapError
from middleware.linked_data.plugin import LinkedDataPlugin


class FakeSitemap:
    """A fake sitemap implementation for LinkedDataPlugin tests."""

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

    def __init__(self, url: str, _client: NiceHttpClient | None = None, _config: Config | None = None) -> None:
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
        client: NiceHttpClient | None = None,
        config: Config | None = None,
    ) -> "FakeDataset":
        """Create a fake dataset from the discovery result."""
        del client, config
        return cls(discovery_result.url)

    async def to_graph(self) -> Graph:
        """Return an empty rdflib Graph, matching Dataset.to_graph()."""
        await asyncio.sleep(0)
        return Graph()


@pytest.mark.asyncio
async def test_linked_data_plugin_run_maps_dataset_to_arc(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=LinkedDataNiceHttpClientConfig(),
    )

    mock_mapper = MagicMock()
    mock_mapper.map_graph.return_value = HarvestedArc(arc_json="mapped:graph")

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FakeSitemap:
        del client
        return FakeSitemap(["https://example.org/dataset/1"])

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr("middleware.linked_data.plugin.Dataset.registry", {DatasetType.html_jsonld: FakeDataset})
    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_mapper",
        staticmethod(lambda _config: mock_mapper),
    )
    monkeypatch.setattr("middleware.linked_data.plugin.NiceHttpClient.ensure_allowed", AsyncMock(return_value=None))

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert results == [HarvestedArc(arc_json="mapped:graph", source_url="https://example.org/dataset/1")]
    mock_mapper.map_graph.assert_called_once()
    (graph_arg,) = mock_mapper.map_graph.call_args.args
    assert isinstance(graph_arg, Graph)


@pytest.mark.asyncio
async def test_linked_data_plugin_run_yields_error_on_dataset_construction_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=LinkedDataNiceHttpClientConfig(),
    )

    class BadDataset:
        @classmethod
        def from_discovery_result(
            cls,
            _discovery_result: UrlDiscoveryResult,
            client: NiceHttpClient | None = None,
            config: Config | None = None,
        ) -> "BadDataset":
            del client, config
            raise RuntimeError("bad dataset")

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FakeSitemap:
        del client
        return FakeSitemap(["https://example.org/dataset/1"])

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr("middleware.linked_data.plugin.Dataset.registry", {DatasetType.html_jsonld: BadDataset})
    monkeypatch.setattr("middleware.linked_data.plugin.NiceHttpClient.ensure_allowed", AsyncMock(return_value=None))

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)


@pytest.mark.asyncio
async def test_linked_data_plugin_run_closes_cleanly_when_generator_is_cancelled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=LinkedDataNiceHttpClientConfig(max_connections=2),
    )

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FakeSitemap:
        del client
        return FakeSitemap(
            [
                "https://example.org/dataset/1",
                "https://example.org/dataset/2",
            ]
        )

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.Dataset.registry",
        {DatasetType.html_jsonld: FakeDataset},
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_mapper",
        staticmethod(
            lambda _config: MagicMock(map_graph=MagicMock(return_value=HarvestedArc(arc_json="mapped:graph")))
        ),
    )
    monkeypatch.setattr("middleware.linked_data.plugin.NiceHttpClient.ensure_allowed", AsyncMock(return_value=None))
    monkeypatch.setattr("middleware.linked_data.plugin.NiceHttpClient.wait_for_host", AsyncMock(return_value=None))

    loop = asyncio.get_running_loop()
    original_handler = loop.get_exception_handler()
    exceptions: list[BaseException | str] = []

    def handle_exception(
        _loop: asyncio.AbstractEventLoop,
        context: Mapping[str, BaseException | str | None],
    ) -> None:
        value = context.get("exception")
        if value is None:
            value = context.get("message", "unknown")
        if not isinstance(value, (BaseException, str)):
            value = str(value)
        exceptions.append(value)

    loop.set_exception_handler(handle_exception)

    try:
        agen = LinkedDataPlugin(config).run()
        first_result = await agen.__anext__()
        assert isinstance(first_result, HarvestedArc)
        assert first_result.arc_json == "mapped:graph"
        await agen.aclose()
        await asyncio.sleep(0)
    finally:
        loop.set_exception_handler(original_handler)

    assert not exceptions


@pytest.mark.asyncio
async def test_linked_data_plugin_run_yields_error_when_robots_disallows_url(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=LinkedDataNiceHttpClientConfig(),
    )

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FakeSitemap:
        del client
        return FakeSitemap(["https://example.org/dataset/1"])

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.NiceHttpClient.ensure_allowed",
        AsyncMock(
            side_effect=RobotsTxtDisallowedError("Dataset URL disallowed by robots.txt: https://example.org/dataset/1")
        ),
    )

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)


@pytest.mark.asyncio
async def test_linked_data_plugin_run_yields_sitemap_error_when_discovery_robots_disallows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Discovery-level robots blocks must yield LinkedDataSitemapError, not ExceptionGroup."""
    config = Config(
        sitemap_url="https://frl.publisso.de/find",
        sitemap_type=SitemapType.regal_find,
        dataset_type=DatasetType.regal_jsonld,
        payload_type=PayloadType.regal_general,
        http=LinkedDataNiceHttpClientConfig(),
    )

    class FailingSitemap:
        async def discover(self) -> AsyncGenerator[UrlDiscoveryResult, None]:
            raise RobotsTxtDisallowedError(
                "URL disallowed by robots.txt: https://frl.publisso.de/find?q=contentType:researchData"
            )
            yield  # pragma: no cover — make this an async generator

        async def get_expected_count(self) -> int | None:
            return None

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FailingSitemap:
        del client
        return FailingSitemap()

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], LinkedDataSitemapError)
    assert "Sitemap discovery failed" in str(results[0])
    assert "robots.txt" in str(results[0])
