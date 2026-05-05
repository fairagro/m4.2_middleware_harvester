"""Plugin generator for INSPIRE-to-ARC harvesting.

Exposes `run_plugin`, the `AsyncGenerator` integration point consumed by the
central Harvester orchestrator. This module contains no CLI entry point.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, cast

from middleware.harvester.errors import HarvesterError, RecordProcessingError
from middleware.inspire.config import Config
from middleware.inspire.csw_client import CSWClient
from middleware.inspire.mapper import InspireMapper
from middleware.inspire.models import InspireRecord

if TYPE_CHECKING:
    from middleware.harvester.plugin_config import PluginConfig

logger = logging.getLogger(__name__)


async def run_plugin(config: "PluginConfig") -> AsyncGenerator[str | HarvesterError, None]:
    """Run the harvest process and yield serialized RO-Crate ARCs or Harvester errors."""
    inspire_config = cast(Config, config)
    # 1. Setup CSW Client
    logger.info("Connecting to CSW at %s...", inspire_config.csw_url)
    csw_client = CSWClient(inspire_config)

    # 2. Setup Mapper
    mapper = InspireMapper()

    # 3. Harvest and Process
    count = 0

    # All parameters are now taken from config
    records_iter: AsyncGenerator[InspireRecord | RecordProcessingError, None] = cast(
        Any, csw_client
    ).get_records_async()

    async for item in records_iter:
        # Yield potential processing errors emitted by the fetcher upstream
        if isinstance(item, RecordProcessingError):
            yield item
            continue

        record = item
        record_url = csw_client.get_record_url(record.identifier)

        # Skip non-dataset records (e.g., services)
        if record.hierarchy and record.hierarchy.lower() not in ["dataset", "series", "nongeographicdataset"]:
            logger.info("Skipping non-dataset record %s (Type: %s)", record.identifier, record.hierarchy)
            continue

        # Log the INSPIRE identifier (UUID)
        logger.debug("Processing record %s (URL: %s)", record.identifier, record_url)

        try:
            # Map to ARC
            arc = mapper.map_record(record)

            # Yield serialized ARC
            json_str = arc.ToROCrateJsonString()
            yield json_str

            logger.info("Successfully generated ARC for record %s - URL: %s", record.identifier, record_url)
            count += 1

        except Exception as e:  # noqa: BLE001
            yield RecordProcessingError(f"Failed to map record: {e}", record.identifier, e)
            continue

    logger.info("Harvest generator exhausted. Processed %d records.", count)


async def get_expected_datasets(config: "PluginConfig") -> int | None:
    """Return the expected total number of datasets for this INSPIRE configuration."""
    inspire_config = cast(Config, config)
    csw_client = CSWClient(inspire_config)
    try:
        return await asyncio.to_thread(csw_client.get_record_count)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to determine expected INSPIRE record count: %s", exc)
        return None
