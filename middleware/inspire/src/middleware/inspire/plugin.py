"""Plugin integration for INSPIRE-to-ARC harvesting."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import ClassVar, cast

from middleware.harvester.errors import HarvesterError, RecordProcessingError, SkippedRecord
from middleware.harvester.plugin_base import HarvestedArc
from middleware.inspire.config import Config
from middleware.inspire.csw_client import CSWClient
from middleware.payload import register_builtin_mappers as _register_builtin_mappers
from middleware.payload.data_mapper import DataMapper
from middleware.payload.inspire.models import InspireRecord
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig
from middleware.payload.mapping_context import MappingContext, as_source_url
from middleware.payload.parsed_payload import ParsedPayload

_ = _register_builtin_mappers

logger = logging.getLogger(__name__)

_HARVESTABLE_HIERARCHIES = frozenset({"dataset", "series", "nongeographicdataset"})


class InspirePlugin:
    """Stateful INSPIRE plugin implementation (structurally satisfies ``Plugin``)."""

    produces: ClassVar[PayloadKind] = PayloadKind.inspire_record

    def __init__(self, config: Config, mapper_config: MapperConfig) -> None:
        """Initialize the plugin with CSW config and repository mapper config."""
        self._config: Config = config
        self._placeholders = mapper_config.placeholders
        self._mapper: DataMapper[MappingContext] = self.create_mapper(mapper_config)
        if self._mapper.accepts != self.produces:
            raise ValueError(
                f"inspire plugin requires mapper accepting {self.produces!r}, got {self._mapper.accepts!r}"
            )

    @staticmethod
    def create_mapper(mapper_config: MapperConfig) -> DataMapper[MappingContext]:
        """Create the shared DataMapper from repository ``mapper`` config.

        The shared registry is context-erased; inspire always passes ``MappingContext``.
        ``registered_class_for_context`` fails closed at construction if the configured
        mapper expects a different context type.
        """
        try:
            mapper_cls = DataMapper.registered_class_for_context(mapper_config.type, MappingContext)
        except KeyError as exc:
            raise ValueError(f"Unsupported mapper type: {mapper_config.type}") from exc
        return cast(DataMapper[MappingContext], mapper_cls.from_config(mapper_config))

    async def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
        """Run the harvest process and yield harvested ARCs, errors, or skips."""
        logger.info("Connecting to CSW at %s...", self._config.csw_url)
        count = 0

        async with CSWClient(self._config, self._placeholders) as csw_client:
            records_iter: AsyncGenerator[InspireRecord | RecordProcessingError, None] = csw_client.get_records_async()

            async for item in records_iter:
                if isinstance(item, RecordProcessingError):
                    yield item
                    continue

                record = item
                record_url = csw_client.get_record_url(record.identifier)

                if record.hierarchy and record.hierarchy.lower() not in _HARVESTABLE_HIERARCHIES:
                    reason = f"Skipping non-dataset record {record.identifier} (hierarchy level: {record.hierarchy})"
                    logger.debug(reason)
                    yield SkippedRecord(reason, record_url)
                    continue

                logger.debug("Processing record %s (URL: %s)", record.identifier, record_url)

                try:
                    payload = ParsedPayload(
                        kind=PayloadKind.inspire_record,
                        value=record,
                        identifier=record.identifier,
                    )
                    context = MappingContext(
                        source_url=as_source_url(record_url),
                        harvest_source_id=record.identifier,
                    )
                    harvested_items = list(self._mapper.map(payload, context))
                    if not harvested_items:
                        yield RecordProcessingError(
                            f"Mapper produced no ARC for {record.identifier}",
                            record.identifier,
                            url=record_url,
                        )
                        continue
                    for harvested in harvested_items:
                        yield harvested
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
                        url=record_url,
                    )
                    continue

        logger.info("Harvest generator exhausted. Processed %d records.", count)

    async def get_expected_datasets(self) -> int | None:
        """Return the expected total number of datasets for this INSPIRE configuration."""
        try:
            async with CSWClient(self._config, self._placeholders) as csw_client:
                return await csw_client.get_record_count_async()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to determine expected INSPIRE record count: %s", exc)
            return None
