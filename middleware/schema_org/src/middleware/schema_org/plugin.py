"""Schema.org harvester plugin integration point."""

import asyncio
import logging
from collections.abc import AsyncGenerator

import httpx

from middleware.harvester.errors import HarvesterError, RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.harvester.plugin_base import Plugin

from .config import Config
from .dataset import Dataset, DiscoveryResult
from .dataset.html_jsonld import HtmlJsonLdDataset  # noqa: F401
from .errors import SchemaOrgError
from .schema_org_mapper import SchemaOrgMapper
from .sitemap import Sitemap

logger = logging.getLogger(__name__)


class SchemaOrgPlugin(Plugin):
    """Stateful Schema.org plugin implementation."""

    def __init__(self, config: Config) -> None:
        """Initialize the plugin with its parsed configuration."""
        self._config: Config = config
        self._mapper: SchemaOrgMapper = self.create_mapper(config)

    @staticmethod
    def create_sitemap(config: Config, client: httpx.AsyncClient) -> Sitemap:
        """Create the sitemap implementation for the configured sitemap type."""
        try:
            sitemap_cls = Sitemap.registry[config.sitemap_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported sitemap type: {config.sitemap_type}") from exc

        return sitemap_cls(config, client)

    @staticmethod
    def create_mapper(config: Config) -> SchemaOrgMapper:
        """Create the mapper implementation for the configured payload type."""
        try:
            mapper_cls = SchemaOrgMapper.registry[config.payload_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported payload type: {config.payload_type}") from exc

        return mapper_cls()

    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count for this Schema.org source."""
        async with NiceHttpClient(self._config.http) as nice_http:
            sitemap = self.create_sitemap(self._config, client=nice_http.client)
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
    ) -> str | RecordProcessingError:
        try:
            dataset_cls = Dataset.registry[self._config.dataset_type]
            dataset = dataset_cls.from_discovery_result(
                discovery_result,
                client=nice_http,
                config=self._config,
            )
        except (SchemaOrgError, RuntimeError, ValueError, OSError) as exc:  # pragma: no cover
            return RecordProcessingError(
                f"Failed to construct dataset from discovery result {discovery_result}: {exc}",
                str(discovery_result),
                exc,
            )

        try:
            graph = await dataset.to_graph()
            return await asyncio.to_thread(self._mapper.map_graph, graph)
        except (SchemaOrgError, RuntimeError, ValueError, OSError) as exc:  # pragma: no cover
            return RecordProcessingError(
                f"Failed to map dataset {dataset.identifier}: {exc}",
                dataset.identifier,
                exc,
            )

    async def _run_with_task_group(
        self,
        sitemap: Sitemap,
        nice_http: NiceHttpClient,
        worker_tasks: int,
    ) -> AsyncGenerator[str | HarvesterError, None]:
        results: asyncio.Queue[str | HarvesterError] = asyncio.Queue()
        semaphore = asyncio.Semaphore(worker_tasks)
        discovery_finished = False

        async def worker(discovery_result: DiscoveryResult) -> None:
            try:
                result = await self._process_result(discovery_result, nice_http)
            except (RuntimeError, ValueError, OSError, httpx.HTTPError) as exc:
                result = RecordProcessingError(
                    f"Failed to process discovery result {discovery_result}: {exc}",
                    str(discovery_result),
                    exc,
                )
            await results.put(result)
            semaphore.release()

        async with asyncio.TaskGroup() as task_group:

            async def producer() -> None:
                nonlocal discovery_finished
                async for discovery_result in sitemap.discover():
                    await semaphore.acquire()
                    task_group.create_task(worker(discovery_result))
                discovery_finished = True

            # Run the discovery producer inside the TaskGroup so its lifecycle and
            # exceptions are managed together with the worker tasks.
            # This keeps discovery and result streaming concurrent.
            task_group.create_task(producer())

            while not discovery_finished or not results.empty():
                payload = await results.get()
                try:
                    yield payload
                except GeneratorExit:
                    return

    async def run(self) -> AsyncGenerator[str | HarvesterError, None]:
        """Run the plugin and yield serialized ARC RO-Crate payloads."""
        async with NiceHttpClient(self._config.http) as nice_http:
            sitemap = self.create_sitemap(self._config, client=nice_http.client)
            worker_tasks = self._config.effective_worker_tasks
            async for item in self._run_with_task_group(sitemap, nice_http, worker_tasks):
                yield item
