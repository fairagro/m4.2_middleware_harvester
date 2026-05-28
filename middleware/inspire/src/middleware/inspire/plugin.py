"""Plugin integration for INSPIRE-to-ARC harvesting."""

import logging
from collections.abc import AsyncGenerator

from middleware.harvester.errors import HarvesterError, RecordProcessingError
from middleware.harvester.plugin_base import Plugin
from middleware.inspire.config import Config
from middleware.inspire.csw_client import CSWClient
from middleware.inspire.mapper import InspireMapper
from middleware.inspire.models import InspireRecord

logger = logging.getLogger(__name__)


class InspirePlugin(Plugin):
    """Stateful INSPIRE plugin implementation."""

    def __init__(self, config: Config) -> None:
        """Initialize the plugin with its parsed configuration."""
        self._config: Config = config

    async def run(self) -> AsyncGenerator[tuple[str, str | None] | HarvesterError, None]:
        """Run the harvest process and yield (arc_json, source_url) pairs or errors."""
        logger.info("Connecting to CSW at %s...", self._config.csw_url)
        csw_client = CSWClient(self._config)
        mapper = InspireMapper()
        count = 0

        records_iter: AsyncGenerator[InspireRecord | RecordProcessingError, None] = csw_client.get_records_async()

        async for item in records_iter:
            if isinstance(item, RecordProcessingError):
                yield item
                continue

            record = item
            record_url = csw_client.get_record_url(record.identifier)

            if record.hierarchy and record.hierarchy.lower() not in [
                "dataset",
                "series",
                "nongeographicdataset",
            ]:
                logger.info(
                    "Skipping non-dataset record %s (Type: %s)",
                    record.identifier,
                    record.hierarchy,
                )
                continue

            logger.debug("Processing record %s (URL: %s)", record.identifier, record_url)

            try:
                arc = mapper.map_record(record)
                json_str = arc.ToROCrateJsonString()
                yield json_str, record_url
                logger.info(
                    "Successfully generated ARC for record %s - URL: %s",
                    record.identifier,
                    record_url,
                )
                count += 1
            except Exception as exc:  # noqa: BLE001
                yield RecordProcessingError(
                    f"Failed to map record: {exc}",
                    record.identifier,
                    exc,
                )
                continue

        logger.info("Harvest generator exhausted. Processed %d records.", count)

    async def get_expected_datasets(self) -> int | None:
        """Return the expected total number of datasets for this INSPIRE configuration."""
        csw_client = CSWClient(self._config)
        try:
            return await csw_client.get_record_count_async()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to determine expected INSPIRE record count: %s", exc)
            return None
