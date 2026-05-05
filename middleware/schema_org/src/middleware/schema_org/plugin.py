"""Schema.org harvester plugin integration point."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, cast

import httpx

from middleware.harvester.errors import HarvesterError, RecordProcessingError

from .config import Config
from .dataset import Dataset, DiscoveryResult
from .dataset.html_jsonld import HtmlJsonLdDataset  # noqa: F401
from .errors import SchemaOrgError
from .schema_org_mapper import SchemaOrgMapper
from .sitemap import Sitemap

if TYPE_CHECKING:
    from middleware.harvester.plugin_config import PluginConfig


def create_sitemap(config: Config, client: httpx.AsyncClient) -> Sitemap:
    """Create the sitemap implementation for the configured sitemap type."""
    try:
        sitemap_cls = Sitemap.registry[config.sitemap_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported sitemap type: {config.sitemap_type}") from exc

    try:
        Dataset.registry[config.dataset_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported dataset type: {config.dataset_type}") from exc

    return sitemap_cls(config, client)


def create_mapper(config: Config) -> SchemaOrgMapper:
    """Create the mapper implementation for the configured payload type."""
    try:
        mapper_cls = SchemaOrgMapper.registry[config.payload_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported payload type: {config.payload_type}") from exc

    return mapper_cls()


async def get_expected_datasets(config: "PluginConfig") -> int | None:
    """Return the expected dataset count for this Schema.org source."""
    schema_config = cast(Config, config)
    limits = httpx.Limits(
        max_connections=schema_config.max_connections,
        max_keepalive_connections=schema_config.max_connections,
    )
    async with httpx.AsyncClient(timeout=schema_config.timeout, limits=limits) as http_client:
        sitemap = create_sitemap(schema_config, client=http_client)
        try:
            return await sitemap.get_expected_count()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to determine expected dataset count for sitemap %s: %s",
                schema_config.sitemap_url,
                exc,
            )
            return None


logger = logging.getLogger(__name__)


async def run_plugin(config: "PluginConfig") -> AsyncGenerator[str | HarvesterError, None]:
    """Run the Schema.org harvest plugin and yield serialized ARC RO-Crate payloads."""
    schema_config = cast(Config, config)
    mapper = create_mapper(schema_config)

    limits = httpx.Limits(
        max_connections=schema_config.max_connections,
        max_keepalive_connections=schema_config.max_connections,
    )
    async with httpx.AsyncClient(timeout=schema_config.timeout, limits=limits) as http_client:
        sitemap = create_sitemap(schema_config, client=http_client)
        semaphore = asyncio.Semaphore(schema_config.max_connections)

        async def _process_result(discovery_result: "DiscoveryResult") -> str | RecordProcessingError:
            await semaphore.acquire()
            try:
                try:
                    dataset_cls = Dataset.registry[schema_config.dataset_type]
                    dataset = dataset_cls.from_discovery_result(
                        discovery_result,
                        client=http_client,
                        config=schema_config,
                    )
                except (SchemaOrgError, RuntimeError, ValueError, OSError) as exc:  # pragma: no cover
                    return RecordProcessingError(
                        f"Failed to construct dataset from discovery result {discovery_result}: {exc}",
                        str(discovery_result),
                        exc,
                    )

                try:
                    graph = await dataset.to_graph()
                    return mapper.map_graph(graph)
                except (SchemaOrgError, RuntimeError, ValueError, OSError) as exc:  # pragma: no cover
                    return RecordProcessingError(
                        f"Failed to map dataset {dataset.identifier}: {exc}",
                        dataset.identifier,
                        exc,
                    )
            finally:
                semaphore.release()

        pending: set[asyncio.Task[str | RecordProcessingError]] = set()
        async with asyncio.TaskGroup() as task_group:
            async for discovery_result in sitemap.discover():
                task = task_group.create_task(_process_result(discovery_result))
                pending.add(task)
                if len(pending) >= schema_config.max_connections:
                    done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                    for finished in done:
                        yield finished.result()

            while pending:
                done, pending = await asyncio.wait(pending)
                for finished in done:
                    yield finished.result()
