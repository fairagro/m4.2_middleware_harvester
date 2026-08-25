"""Linked Data harvester plugin integration point."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from dataclasses import replace

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
    ) -> HarvestedArc | RecordProcessingError | SkippedRecord:
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
            return RecordProcessingError(
                (
                    f"Failed to construct dataset from "
                    f"{type(discovery_result).__name__} {discovery_result.identifier}: {exc}"
                ),
                discovery_result.identifier,
                exc,
                url=source_url,
            )

        try:
            graph = await dataset.to_graph()
            mapping_context = MappingContext(
                source_url=source_url,
                harvest_source_id=harvest_source_id,
            )
            harvested = await asyncio.to_thread(
                self._mapper.map_graph,
                graph,
                mapping_context,
            )
            return replace(harvested, source_url=source_url)
        except (LinkedDataError, RuntimeError, ValueError, OSError) as exc:
            return RecordProcessingError(
                f"Failed to map dataset {dataset.identifier}: {exc}",
                dataset.identifier,
                exc,
                url=source_url,
            )

    async def _run_with_task_group(
        self,
        sitemap: Sitemap,
        nice_http: NiceHttpClient,
        worker_tasks: int,
    ) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
        results: asyncio.Queue[HarvestedArc | HarvesterError | SkippedRecord] = asyncio.Queue()
        semaphore = asyncio.Semaphore(worker_tasks)
        discovery_finished = False
        active_workers = 0

        async def worker(discovery_result: DiscoveryResult) -> None:
            nonlocal active_workers
            # Always release the permit and decrement the counter, including on
            # CancelledError — otherwise the consumer loop can deadlock waiting
            # for active_workers to reach 0 while results.get() never completes.
            try:
                try:
                    result = await self._process_result(discovery_result, nice_http)
                except (RuntimeError, ValueError, OSError, httpx.HTTPError) as exc:
                    result = RecordProcessingError(
                        (f"Failed to process {type(discovery_result).__name__} {discovery_result.identifier}: {exc}"),
                        discovery_result.identifier,
                        exc,
                        url=(discovery_result.identifier if isinstance(discovery_result, UrlDiscoveryResult) else None),
                    )
                await results.put(result)
            finally:
                active_workers -= 1
                semaphore.release()

        async with asyncio.TaskGroup() as task_group:

            async def producer() -> None:
                nonlocal discovery_finished, active_workers
                try:
                    async for item in sitemap.discover():
                        # Inspire-style: discovery already yields shared harvester signals.
                        if isinstance(item, (RecordProcessingError, SkippedRecord)):
                            await results.put(item)
                            continue
                        await semaphore.acquire()
                        active_workers += 1
                        task_group.create_task(worker(item))
                except (
                    LinkedDataError,
                    RobotsTxtDisallowedError,
                    RuntimeError,
                    ValueError,
                    OSError,
                    httpx.HTTPError,
                ) as exc:
                    # Discovery-level failure must not escape TaskGroup as ExceptionGroup;
                    # yield a HarvesterError so the orchestrator can report it cleanly.
                    if isinstance(exc, HarvesterError):
                        await results.put(exc)
                    else:
                        await results.put(
                            LinkedDataSitemapError(f"Sitemap discovery failed for {self._config.sitemap_url}: {exc}")
                        )
                finally:
                    discovery_finished = True

            # Run the discovery producer inside the TaskGroup so its lifecycle and
            # exceptions are managed together with the worker tasks.
            # This keeps discovery and result streaming concurrent.
            task_group.create_task(producer())

            while not discovery_finished or active_workers > 0 or not results.empty():
                payload = await results.get()
                try:
                    yield payload
                except GeneratorExit:
                    return

    async def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
        """Run the plugin and yield harvested ARCs, errors, or skips."""
        async with NiceHttpClient(self._config.http) as nice_http:
            sitemap = self.create_sitemap(self._config, client=nice_http)
            worker_tasks = self._config.effective_worker_tasks
            async for item in self._run_with_task_group(sitemap, nice_http, worker_tasks):
                yield item
