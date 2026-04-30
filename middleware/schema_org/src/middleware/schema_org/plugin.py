"""Schema.org harvester plugin integration point."""

import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, cast

from middleware.harvester.errors import HarvesterError, RecordProcessingError
from middleware.schema_org.config import (
    Config,
    DatasetType,
    PayloadType,
    SitemapType,
)
from middleware.schema_org.interfaces import DummySchemaOrgMapper, DummySitemap, SchemaOrgMapper, Sitemap

if TYPE_CHECKING:
    from middleware.harvester.plugin_config import PluginConfig


def create_sitemap(config: Config) -> Sitemap:
    """Create the sitemap implementation for the configured sitemap type."""
    if config.sitemap_type == SitemapType.xml:
        if config.dataset_type == DatasetType.dummy:
            return DummySitemap(config)
        raise ValueError(f"Unsupported dataset type: {config.dataset_type}")

    raise ValueError(f"Unsupported sitemap type: {config.sitemap_type}")


def create_mapper(config: Config) -> SchemaOrgMapper:
    """Create the mapper implementation for the configured payload type."""
    if config.payload_type == PayloadType.dummy:
        return DummySchemaOrgMapper()

    raise ValueError(f"Unsupported payload type: {config.payload_type}")


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
