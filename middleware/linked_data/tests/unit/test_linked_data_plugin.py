"""Unit tests for the Linked Data plugin entrypoint."""

import asyncio
from collections.abc import AsyncGenerator, Mapping
from dataclasses import dataclass
from typing import cast
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
from middleware.linked_data.pipeline import PipelineResult, ResultsQueueHook
from middleware.linked_data.plugin import LinkedDataPlugin
from middleware.linked_data.sitemap import Sitemap


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
    mock_mapper.map_graph.return_value = [HarvestedArc(arc_json="mapped:graph")]

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
    graph_arg, context_arg = mock_mapper.map_graph.call_args.args
    assert isinstance(graph_arg, Graph)
    assert context_arg.source_url == "https://example.org/dataset/1"


@pytest.mark.asyncio
async def test_linked_data_plugin_forwards_harvest_source_id_to_mapper(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=LinkedDataNiceHttpClientConfig(),
    )

    class FakeSitemapWithCatalogId:
        async def discover(self) -> AsyncGenerator[UrlDiscoveryResult, None]:
            yield UrlDiscoveryResult(
                "https://www.openagrar.de/receive/openagrar_mods_00107322",
                harvest_source_id="openagrar_mods_00107322",
            )

        async def get_expected_count(self) -> int | None:
            return 1

    mock_mapper = MagicMock()
    mock_mapper.map_graph.return_value = [HarvestedArc(arc_json="mapped:graph")]

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FakeSitemapWithCatalogId:
        del client
        return FakeSitemapWithCatalogId()

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

    assert len(results) == 1
    mock_mapper.map_graph.assert_called_once()
    _graph_arg, context_arg = mock_mapper.map_graph.call_args.args
    assert context_arg.harvest_source_id == "openagrar_mods_00107322"


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
            lambda _config: MagicMock(map_graph=MagicMock(return_value=[HarvestedArc(arc_json="mapped:graph")]))
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
        first_result = await anext(agen)
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


def _install_plugin_fakes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    sitemap: FakeSitemap | object,
    dataset_cls: type = FakeDataset,
    mapper: MagicMock | None = None,
) -> MagicMock:
    """Patch LinkedDataPlugin dependencies for pipeline behaviour tests."""
    mock_mapper = mapper or MagicMock(map_graph=MagicMock(return_value=[HarvestedArc(arc_json="mapped:graph")]))

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> object:
        del client
        return sitemap

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.Dataset.registry",
        {DatasetType.html_jsonld: dataset_cls},
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_mapper",
        staticmethod(lambda _config: mock_mapper),
    )
    monkeypatch.setattr("middleware.linked_data.plugin.NiceHttpClient.ensure_allowed", AsyncMock(return_value=None))
    monkeypatch.setattr("middleware.linked_data.plugin.NiceHttpClient.wait_for_host", AsyncMock(return_value=None))
    return mock_mapper


@dataclass
class _PipelineMetrics:
    """Observed concurrency while exercising the linked-data pipeline."""

    concurrent_maps: int = 0
    peak_concurrent_maps: int = 0
    peak_pipeline: int = 0
    pending_puts: int = 0
    results_queue: asyncio.Queue[object] | None = None

    def record_pipeline_size(self) -> None:
        if self.results_queue is not None:
            # Include workers blocked on put after mapping finished — otherwise
            # peak undercounts discovery items still holding a semaphore slot.
            in_pipeline = self.concurrent_maps + self.pending_puts + self.results_queue.qsize()
            self.peak_pipeline = max(self.peak_pipeline, in_pipeline)


def _install_pipeline_tracking(monkeypatch: pytest.MonkeyPatch, worker_tasks: int) -> _PipelineMetrics:
    """Observe queue depth and worker concurrency via the pipeline results-queue hook."""
    metrics = _PipelineMetrics()
    original_run = LinkedDataPlugin._run_with_task_group  # noqa: SLF001

    def capture_results_queue(queue: asyncio.Queue[object]) -> None:
        assert queue.maxsize == worker_tasks
        metrics.results_queue = queue
        original_put = queue.put

        async def tracked_put(item: object) -> None:
            metrics.pending_puts += 1
            metrics.record_pipeline_size()
            try:
                await original_put(item)
            finally:
                metrics.pending_puts -= 1
                metrics.record_pipeline_size()

        queue.put = tracked_put  # type: ignore[method-assign]

    async def tracking_run(
        self: LinkedDataPlugin,
        sitemap: Sitemap,
        nice_http: NiceHttpClient,
        worker_tasks_arg: int,
        *,
        on_results_queue: object | None = None,
    ) -> AsyncGenerator[PipelineResult, None]:
        del on_results_queue

        async for item in original_run(
            self,
            sitemap,
            nice_http,
            worker_tasks_arg,
            on_results_queue=cast(ResultsQueueHook, capture_results_queue),
        ):
            metrics.record_pipeline_size()
            yield item

    async def slow_process(
        _self: LinkedDataPlugin,
        discovery_result: UrlDiscoveryResult,
        _nice_http: NiceHttpClient,
    ) -> list[HarvestedArc]:
        metrics.concurrent_maps += 1
        metrics.peak_concurrent_maps = max(metrics.peak_concurrent_maps, metrics.concurrent_maps)
        metrics.record_pipeline_size()
        try:
            await asyncio.sleep(0.02)
            return [HarvestedArc(arc_json=f"mapped:{discovery_result.url}", source_url=discovery_result.url)]
        finally:
            metrics.concurrent_maps -= 1
            metrics.record_pipeline_size()

    monkeypatch.setattr(LinkedDataPlugin, "_run_with_task_group", tracking_run)
    monkeypatch.setattr(LinkedDataPlugin, "_process_result", slow_process)
    return metrics


async def _drain_with_slow_consumer(
    agen: AsyncGenerator[PipelineResult, None],
    catalog_size: int,
    *,
    item_delay: float,
) -> list[HarvestedArc]:
    """Consume a plugin stream one item at a time with a delay between reads."""
    consumer_gate = asyncio.Event()
    consumer_gate.set()
    collected: list[HarvestedArc] = []
    try:
        for _ in range(catalog_size):
            await consumer_gate.wait()
            consumer_gate.clear()
            item = await anext(agen)
            assert isinstance(item, HarvestedArc)
            collected.append(item)
            await asyncio.sleep(item_delay)
            consumer_gate.set()
    finally:
        await agen.aclose()
    return collected


@pytest.mark.asyncio
async def test_linked_data_plugin_bounds_pipeline_under_slow_consumer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Discovery items in workers plus queue slots must not exceed 2 × worker_tasks."""
    worker_tasks = 2
    catalog_size = 12
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=LinkedDataNiceHttpClientConfig(max_connections=worker_tasks),
    )
    urls = [f"https://example.org/dataset/{index}" for index in range(catalog_size)]
    _install_plugin_fakes(monkeypatch, sitemap=FakeSitemap(urls))
    metrics = _install_pipeline_tracking(monkeypatch, worker_tasks)

    collected = await _drain_with_slow_consumer(LinkedDataPlugin(config).run(), catalog_size, item_delay=0.03)

    assert len(collected) == catalog_size
    assert metrics.results_queue is not None
    assert metrics.peak_concurrent_maps <= worker_tasks
    assert metrics.peak_pipeline <= 2 * worker_tasks


@pytest.mark.asyncio
async def test_linked_data_plugin_empty_sitemap_exits_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty discovery catalog must complete without hanging on results.get()."""
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=LinkedDataNiceHttpClientConfig(max_connections=2),
    )
    _install_plugin_fakes(monkeypatch, sitemap=FakeSitemap([]))

    async def collect() -> list[PipelineResult]:
        return [item async for item in LinkedDataPlugin(config).run()]

    collected = await asyncio.wait_for(collect(), timeout=2.0)
    assert collected == []


@pytest.mark.asyncio
async def test_linked_data_plugin_early_aclose_stops_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    """Closing the generator early must not map the full catalog."""
    catalog_size = 50
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=LinkedDataNiceHttpClientConfig(max_connections=4),
    )
    urls = [f"https://example.org/dataset/{index}" for index in range(catalog_size)]
    _install_plugin_fakes(monkeypatch, sitemap=FakeSitemap(urls))

    process_count = 0

    async def slow_process(
        _self: LinkedDataPlugin,
        discovery_result: UrlDiscoveryResult,
        _nice_http: NiceHttpClient,
    ) -> list[HarvestedArc]:
        nonlocal process_count
        process_count += 1
        await asyncio.sleep(0.05)
        return [HarvestedArc(arc_json=f"mapped:{discovery_result.url}", source_url=discovery_result.url)]

    monkeypatch.setattr(LinkedDataPlugin, "_process_result", slow_process)

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
        first_result = await anext(agen)
        assert isinstance(first_result, HarvestedArc)
        await agen.aclose()
        await asyncio.sleep(0.1)
    finally:
        loop.set_exception_handler(original_handler)

    assert process_count < catalog_size // 2
    assert not exceptions


@pytest.mark.asyncio
async def test_linked_data_plugin_preserves_arrival_order_under_backpressure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Yield order must stay discovery order when mapping runs sequentially."""
    worker_tasks = 1
    catalog_size = 8
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=LinkedDataNiceHttpClientConfig(max_connections=worker_tasks),
    )
    urls = [f"https://example.org/dataset/{index}" for index in range(catalog_size)]
    _install_plugin_fakes(monkeypatch, sitemap=FakeSitemap(urls))

    async def slow_process(
        _self: LinkedDataPlugin,
        discovery_result: UrlDiscoveryResult,
        _nice_http: NiceHttpClient,
    ) -> list[HarvestedArc]:
        del _nice_http
        await asyncio.sleep(0.01)
        return [HarvestedArc(arc_json=f"mapped:{discovery_result.url}", source_url=discovery_result.url)]

    monkeypatch.setattr(LinkedDataPlugin, "_process_result", slow_process)

    agen = LinkedDataPlugin(config).run()
    collected: list[str] = []
    try:
        for _ in range(catalog_size):
            item = await anext(agen)
            assert isinstance(item, HarvestedArc)
            collected.append(item.source_url or "")
            await asyncio.sleep(0.02)
    finally:
        await agen.aclose()

    assert collected == urls
