"""OAI-PMH harvest plugin: ListRecords → PayloadParser → DataMapper."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator, Iterator
from dataclasses import replace

import middleware.parsing.register_builtin_parsers as _register_parsers
import middleware.payload.linked_data_mapper.register_builtins as _register_builtin_mappers
from middleware.harvester.errors import HarvesterError, RecordProcessingError, SkippedRecord
from middleware.harvester.plugin_base import HarvestedArc
from middleware.oai_pmh.client import RateLimiter, check_robots_allowed, create_scythe
from middleware.oai_pmh.config import Config
from middleware.oai_pmh.errors import OaiPmhError, OaiPmhProtocolError, OaiPmhRobotsDisallowedError
from middleware.oai_pmh.harvest import iter_discovery_units
from middleware.parsing.discovery import XmlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_config import ParserConfig
from middleware.payload.linked_data_mapper import LinkedDataMapper, MappingContext
from middleware.payload.mapper_config import MapperConfig

_ = (_register_parsers, _register_builtin_mappers)

logger = logging.getLogger(__name__)


class OaiPmhPlugin:
    """Stateful OAI-PMH plugin (structurally satisfies ``Plugin``)."""

    def __init__(self, config: Config, mapper_config: MapperConfig, parser_config: ParserConfig) -> None:
        """Initialize with plugin + repository mapper/parser configuration."""
        self._config = config
        self._mapper: LinkedDataMapper = self.create_mapper(mapper_config)
        self._parser_cls: type[PayloadParser] = self.create_parser_class(parser_config)
        if self._parser_cls.produces != self._mapper.accepts:
            raise ValueError(
                f"parser {parser_config.type} produces {self._parser_cls.produces!r}, "
                f"but mapper accepts {self._mapper.accepts!r}"
            )

    @staticmethod
    def create_parser_class(parser_config: ParserConfig) -> type[PayloadParser]:
        """Resolve the PayloadParser implementation for the configured parser type."""
        try:
            return PayloadParser.registry[parser_config.type]
        except KeyError as exc:
            raise ValueError(f"Unsupported parser type: {parser_config.type}") from exc

    @staticmethod
    def create_mapper(mapper_config: MapperConfig) -> LinkedDataMapper:
        """Create the mapper from repository ``mapper`` config (shared registry)."""
        try:
            mapper_cls = LinkedDataMapper.registered_class(mapper_config.type)
        except KeyError as exc:
            raise ValueError(f"Unsupported mapper type: {mapper_config.type}") from exc
        return mapper_cls.from_config(mapper_config)

    async def get_expected_datasets(self) -> int | None:
        """Return ``None`` unless a cheap reliable complete-list size is available."""
        _ = self
        return None

    def _sync_discover(self) -> Iterator[XmlDiscoveryResult | SkippedRecord | RecordProcessingError]:
        check_robots_allowed(self._config)
        scythe = create_scythe(self._config)
        try:
            yield from iter_discovery_units(
                self._config,
                scythe=scythe,
                rate_limiter=RateLimiter(self._config.max_requests_per_second),
            )
        finally:
            scythe.close()

    async def _process_unit(
        self,
        discovery: XmlDiscoveryResult,
    ) -> HarvestedArc | RecordProcessingError:
        parser = self._parser_cls()
        try:
            payload = await parser.parse(discovery, client=None, config=self._config)
        except (ParserError, OaiPmhError, RuntimeError, ValueError, OSError) as exc:
            return RecordProcessingError(
                f"Failed to parse OAI record {discovery.identifier}: {exc}",
                discovery.identifier,
                exc,
                url=discovery.identifier,
            )

        if payload.kind != self._mapper.accepts:
            return RecordProcessingError(
                (
                    f"Payload kind {payload.kind!r} incompatible with mapper "
                    f"accepts {self._mapper.accepts!r} for {payload.identifier}"
                ),
                payload.identifier,
                url=discovery.identifier,
            )

        try:
            mapping_context = MappingContext(source_url=discovery.identifier, harvest_source_id=discovery.identifier)
            harvested_items = await asyncio.to_thread(
                lambda: list(self._mapper.map(payload, mapping_context)),
            )
            if not harvested_items:
                return RecordProcessingError(
                    f"Mapper produced no ARC for {payload.identifier}",
                    payload.identifier,
                    url=discovery.identifier,
                )
            # OAI typically maps 1:1; yield the first harvested item with source identity.
            first = harvested_items[0]
            return replace(first, source_url=discovery.identifier)
        except (OaiPmhError, RuntimeError, ValueError, OSError) as exc:
            return RecordProcessingError(
                f"Failed to map OAI record {payload.identifier}: {exc}",
                payload.identifier,
                exc,
                url=discovery.identifier,
            )

    async def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
        """Run the plugin and yield harvested ARCs, errors, or skips."""
        try:
            units = await asyncio.to_thread(lambda: list(self._sync_discover()))
        except OaiPmhRobotsDisallowedError as exc:
            yield exc
            return
        except OaiPmhProtocolError as exc:
            yield exc
            return
        except Exception as exc:  # noqa: BLE001
            yield OaiPmhProtocolError(f"OAI harvest failed for {self._config.endpoint_url}: {exc}")
            return

        for unit in units:
            if isinstance(unit, (SkippedRecord, RecordProcessingError)):
                yield unit
                continue
            yield await self._process_unit(unit)
