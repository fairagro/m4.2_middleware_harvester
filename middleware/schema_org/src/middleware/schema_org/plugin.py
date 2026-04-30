"""Schema.org harvester plugin integration point."""

import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, cast

import httpx

from middleware.harvester.errors import HarvesterError, RecordProcessingError
from middleware.schema_org.config import Config
from middleware.schema_org.dataset import Dataset
from middleware.schema_org.schema_org_mapper import SchemaOrgMapper
from middleware.schema_org.sitemap import Sitemap

if TYPE_CHECKING:
    from middleware.harvester.plugin_config import PluginConfig


def create_sitemap(config: Config, client: httpx.AsyncClient | None = None) -> Sitemap:
    """Create the sitemap implementation for the configured sitemap type."""
    try:
        sitemap_cls = Sitemap.registry[config.sitemap_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported sitemap type: {config.sitemap_type}") from exc

    try:
        dataset_cls = Dataset.registry[config.dataset_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported dataset type: {config.dataset_type}") from exc

    return sitemap_cls(config, dataset_factory=dataset_cls, client=client)


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
    sitemap = create_sitemap(schema_config)
    mapper = create_mapper(schema_config)

    try:
        async for dataset in sitemap.discover():
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
