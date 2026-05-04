"""Schema.org harvester plugin integration point."""

import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, cast

import httpx

from middleware.harvester.errors import HarvesterError, RecordProcessingError
from middleware.schema_org import html_jsonld_dataset  # noqa: F401
from middleware.schema_org.config import Config
from middleware.schema_org.dataset import Dataset
from middleware.schema_org.schema_org_mapper import SchemaOrgMapper
from middleware.schema_org.sitemap import Sitemap

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
        try:
            async for discovery_result in sitemap.discover():
                try:
                    dataset_cls = Dataset.registry[schema_config.dataset_type]
                    dataset = dataset_cls.from_discovery_result(discovery_result)
                except (RuntimeError, ValueError, OSError) as exc:  # pragma: no cover
                    yield RecordProcessingError(
                        f"Failed to construct dataset from discovery result {discovery_result}: {exc}",
                        str(discovery_result),
                        exc,
                    )
                    continue

                try:
                    graph = await dataset.to_graph()
                    yield mapper.map_graph(graph)
                except (RuntimeError, ValueError, OSError) as exc:  # pragma: no cover
                    yield RecordProcessingError(
                        f"Failed to map dataset {dataset.identifier}: {exc}",
                        dataset.identifier,
                        exc,
                    )
        except (RuntimeError, ValueError, OSError) as exc:  # pragma: no cover
            logger.error("Schema.org harvest failed: %s", exc)
