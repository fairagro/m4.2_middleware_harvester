"""Schema.org harvester plugin integration point."""

import asyncio
import logging
from collections.abc import AsyncGenerator

import httpx

from middleware.harvester.errors import HarvesterError, RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient, RobotsTxtDisallowedError
from middleware.harvester.plugin_base import Plugin

from .config import Config
from .dataset import Dataset, DiscoveryResult, UrlDiscoveryResult
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
        self._http_config = config.http
        self._semaphore = asyncio.Semaphore(self._http_config.max_connections)

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
        await self._semaphore.acquire()
        try:
            if not isinstance(discovery_result, UrlDiscoveryResult):
                return RecordProcessingError(
                    f"Unsupported discovery result type: {type(discovery_result).__name__}",
                    str(discovery_result),
                    RuntimeError("unsupported discovery result type"),
                )

            try:
                await nice_http.ensure_allowed(discovery_result.url)
            except RobotsTxtDisallowedError as exc:
                return RecordProcessingError(
                    str(exc),
                    discovery_result.url,
                    exc,
                )

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

            await nice_http.wait_for_host(discovery_result.url)

            try:
                graph = await dataset.to_graph()
                return self._mapper.map_graph(graph)
            except (SchemaOrgError, RuntimeError, ValueError, OSError) as exc:  # pragma: no cover
                return RecordProcessingError(
                    f"Failed to map dataset {dataset.identifier}: {exc}",
                    dataset.identifier,
                    exc,
                )
        finally:
            self._semaphore.release()

    async def run(self) -> AsyncGenerator[str | HarvesterError, None]:
        """Run the plugin and yield serialized ARC RO-Crate payloads."""
        async with NiceHttpClient(self._config.http) as nice_http:
            sitemap = self.create_sitemap(self._config, client=nice_http.client)
            pending: set[asyncio.Task[str | RecordProcessingError]] = set()
            async with asyncio.TaskGroup() as task_group:
                async for discovery_result in sitemap.discover():
                    task = task_group.create_task(
                        self._process_result(
                            discovery_result,
                            nice_http,
                        )
                    )
                    pending.add(task)
                    if len(pending) >= self._http_config.max_connections:
                        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                        for finished in done:
                            yield finished.result()

                while pending:
                    done, pending = await asyncio.wait(pending)
                    for finished in done:
                        yield finished.result()
