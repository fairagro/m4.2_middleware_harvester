"""Linked Data harvester plugin integration point."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field, replace

import httpx

from middleware.harvester.errors import HarvesterError, RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import NiceHttpClient, RobotsTxtDisallowedError
from middleware.harvester.plugin_base import HarvestedArc

from .config import Config
from .dataset import Dataset, DiscoveryResult, UrlDiscoveryResult
from .dataset.html_jsonld import HtmlJsonLdDataset  # noqa: F401
from .dataset.regal_jsonld import RegalJsonLdDataset  # noqa: F401
from .errors import LinkedDataError, LinkedDataSitemapError
from .linked_data_mapper import LinkedDataMapper, MappingContext
from .sitemap import Sitemap

logger = logging.getLogger(__name__)

PipelineResult = HarvestedArc | HarvesterError | SkippedRecord


class _PipelineComplete:
    """Sentinel: discovery finished and no workers remain."""


_PIPELINE_COMPLETE = _PipelineComplete()
PipelineQueue = asyncio.Queue[PipelineResult | _PipelineComplete]


@dataclass
class _PipelineRun:
    """Mutable state shared by discovery, workers, and the yield loop."""

    discovery_finished: bool = False
    active_workers: int = 0
    complete_signaled: bool = False
    shutdown: asyncio.Event = field(default_factory=asyncio.Event)
    pipeline_tasks: list[asyncio.Task[None]] = field(default_factory=list)

    def request_shutdown(self) -> None:
        """Signal shutdown and cancel all pipeline tasks."""
        self.shutdown.set()
        # Copy: done-callbacks prune the live list while we cancel.
        for task in list(self.pipeline_tasks):
            task.cancel()

    def track_task(self, task: asyncio.Task[None]) -> None:
        """Register a pipeline task and prune it when it completes."""
        self.pipeline_tasks.append(task)

        def _prune(done: asyncio.Task[None]) -> None:
            with contextlib.suppress(ValueError):
                self.pipeline_tasks.remove(done)

        task.add_done_callback(_prune)


@dataclass
class _PipelineContext:
    """Shared queue, concurrency, and HTTP handles for one pipeline run."""

    results: PipelineQueue
    semaphore: asyncio.Semaphore
    task_group: asyncio.TaskGroup
    run: _PipelineRun
    nice_http: NiceHttpClient


class LinkedDataPlugin:
    """Stateful Linked Data plugin implementation (structurally satisfies ``Plugin``)."""

    def __init__(self, config: Config) -> None:
        """Initialize the plugin with its parsed configuration."""
        self._config: Config = config
        self._mapper: LinkedDataMapper = self.create_mapper(config)
        self._dataset_cls: type[Dataset] = self.create_dataset_class(config)

    @staticmethod
    def create_sitemap(config: Config, client: NiceHttpClient) -> Sitemap:
        """Create the sitemap implementation for the configured sitemap type."""
        try:
            sitemap_cls = Sitemap.registry[config.sitemap_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported sitemap type: {config.sitemap_type}") from exc

        return sitemap_cls(config, client)

    @staticmethod
    def create_mapper(config: Config) -> LinkedDataMapper:
        """Create the mapper implementation for the configured payload type."""
        try:
            mapper_cls = LinkedDataMapper.registry[config.payload_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported payload type: {config.payload_type}") from exc

        return mapper_cls.from_config(config)

    @staticmethod
    def create_dataset_class(config: Config) -> type[Dataset]:
        """Resolve the dataset implementation for the configured dataset type."""
        try:
            return Dataset.registry[config.dataset_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported dataset type: {config.dataset_type}") from exc

    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count for this Linked Data source."""
        async with NiceHttpClient(self._config.http) as nice_http:
            sitemap = self.create_sitemap(self._config, client=nice_http)
            try:
                return await sitemap.get_expected_count()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to determine expected dataset count for sitemap %s: %s",
                    self._config.sitemap_url,
                    exc,
                )
                return None

    async def _process_result(
        self,
        discovery_result: DiscoveryResult,
        nice_http: NiceHttpClient,
    ) -> list[HarvestedArc | RecordProcessingError | SkippedRecord]:
        # Only UrlDiscoveryResult carries a real fetched/landing URL; inline
        # payloads (e.g. Regal JSON-LD) yield None and rely on record_id.
        source_url: str | None = None
        harvest_source_id: str | None = None
        if isinstance(discovery_result, UrlDiscoveryResult):
            source_url = discovery_result.url
            harvest_source_id = discovery_result.harvest_source_id
        try:
            dataset = self._dataset_cls.from_discovery_result(
                discovery_result,
                client=nice_http,
                config=self._config,
            )
        except (LinkedDataError, RuntimeError, ValueError, OSError) as exc:
            return [
                RecordProcessingError(
                    (
                        f"Failed to construct dataset from "
                        f"{type(discovery_result).__name__} {discovery_result.identifier}: {exc}"
                    ),
                    discovery_result.identifier,
                    exc,
                    url=source_url,
                )
            ]

        try:
            graph = await dataset.to_graph()
            mapping_context = MappingContext(
                source_url=source_url,
                harvest_source_id=harvest_source_id,
            )
            harvested_items = await asyncio.to_thread(
                lambda: list(self._mapper.map_graph(graph, mapping_context)),
            )
            return [replace(harvested, source_url=source_url) for harvested in harvested_items]
        except (LinkedDataError, RuntimeError, ValueError, OSError) as exc:
            return [
                RecordProcessingError(
                    f"Failed to map dataset {dataset.identifier}: {exc}",
                    dataset.identifier,
                    exc,
                    url=source_url,
                )
            ]

    @staticmethod
    def _processing_failure(
        discovery_result: DiscoveryResult,
        exc: Exception,
    ) -> list[HarvestedArc | RecordProcessingError | SkippedRecord]:
        """Build a single yieldable processing error for a discovery item."""
        url = discovery_result.identifier if isinstance(discovery_result, UrlDiscoveryResult) else None
        return [
            RecordProcessingError(
                f"Failed to process {type(discovery_result).__name__} {discovery_result.identifier}: {exc}",
                discovery_result.identifier,
                exc,
                url=url,
            )
        ]

    def _harvester_error_from_discovery_failure(self, exc: BaseException) -> HarvesterError:
        """Convert a discovery exception into a yieldable harvester error."""
        if isinstance(exc, HarvesterError):
            return exc
        return LinkedDataSitemapError(f"Sitemap discovery failed for {self._config.sitemap_url}: {exc}")

    @staticmethod
    async def _signal_complete_if_idle(ctx: _PipelineContext) -> None:
        """Unblock the consumer when discovery is done and no workers remain.

        Skipped when shutdown is already set: the consumer has left and must not
        block a cancelled worker on a full queue waiting to enqueue the sentinel.
        """
        run = ctx.run
        if not run.discovery_finished or run.active_workers > 0 or run.complete_signaled:
            return
        run.complete_signaled = True
        if run.shutdown.is_set():
            return
        await ctx.results.put(_PIPELINE_COMPLETE)

    async def _run_pipeline_worker(
        self,
        discovery_result: DiscoveryResult,
        ctx: _PipelineContext,
    ) -> None:
        """Fetch/map one discovery item and enqueue each mapped outcome."""
        # Always release the permit and decrement the counter, including on
        # CancelledError — otherwise the consumer loop can deadlock waiting
        # for active_workers to reach 0 while results.get() never completes.
        try:
            try:
                result_items = await self._process_result(discovery_result, ctx.nice_http)
            except (RuntimeError, ValueError, OSError, httpx.HTTPError) as exc:
                result_items = self._processing_failure(discovery_result, exc)
            for result in result_items:
                await ctx.results.put(result)
        finally:
            ctx.run.active_workers -= 1
            ctx.semaphore.release()
            await self._signal_complete_if_idle(ctx)

    async def _run_discovery_producer(
        self,
        sitemap: Sitemap,
        ctx: _PipelineContext,
    ) -> None:
        """Discover datasets and spawn bounded worker tasks."""
        try:
            async for item in sitemap.discover():
                if ctx.run.shutdown.is_set():
                    break
                # Inspire-style: discovery already yields shared harvester signals.
                if isinstance(item, (RecordProcessingError, SkippedRecord)):
                    await ctx.results.put(item)
                    continue
                await ctx.semaphore.acquire()
                if ctx.run.shutdown.is_set():
                    ctx.semaphore.release()
                    break
                ctx.run.active_workers += 1
                ctx.run.track_task(
                    ctx.task_group.create_task(self._run_pipeline_worker(item, ctx)),
                )
        except (LinkedDataError, RobotsTxtDisallowedError, RuntimeError, ValueError, OSError, httpx.HTTPError) as exc:
            # Discovery-level failure must not escape TaskGroup as ExceptionGroup;
            # yield a HarvesterError so the orchestrator can report it cleanly.
            if not ctx.run.shutdown.is_set():
                await ctx.results.put(self._harvester_error_from_discovery_failure(exc))
        finally:
            ctx.run.discovery_finished = True
            await self._signal_complete_if_idle(ctx)

    async def _stream_pipeline_results(
        self,
        results: PipelineQueue,
        _run: _PipelineRun,
    ) -> AsyncGenerator[PipelineResult, None]:
        """Yield queued outcomes until the idle sentinel arrives."""
        while True:
            item = await results.get()
            if isinstance(item, _PipelineComplete):
                return
            yield item

    async def _run_with_task_group(
        self,
        sitemap: Sitemap,
        nice_http: NiceHttpClient,
        worker_tasks: int,
    ) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
        # Bounded queue ties production to consumption: at most worker_tasks queued
        # results plus worker_tasks in-flight workers (2 × worker_tasks total).
        results: PipelineQueue = asyncio.Queue(maxsize=worker_tasks)
        semaphore = asyncio.Semaphore(worker_tasks)
        run = _PipelineRun()

        async with asyncio.TaskGroup() as task_group:
            ctx = _PipelineContext(
                results=results,
                semaphore=semaphore,
                task_group=task_group,
                run=run,
                nice_http=nice_http,
            )
            run.track_task(task_group.create_task(self._run_discovery_producer(sitemap, ctx)))
            try:
                async for payload in self._stream_pipeline_results(results, run):
                    try:
                        yield payload
                    except GeneratorExit:
                        run.request_shutdown()
                        return
            finally:
                run.shutdown.set()

    async def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
        """Run the plugin and yield harvested ARCs, errors, or skips."""
        async with NiceHttpClient(self._config.http) as nice_http:
            sitemap = self.create_sitemap(self._config, client=nice_http)
            worker_tasks = self._config.effective_worker_tasks
            async for item in self._run_with_task_group(sitemap, nice_http, worker_tasks):
                yield item
