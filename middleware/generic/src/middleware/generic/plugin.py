"""Generic harvest plugin: Protocol → PayloadParser → DataMapper."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from dataclasses import replace

import httpx

import middleware.parsing.register_builtin_parsers as _register_html_jsonld_parser
from middleware.generic.config import Config, ProtocolType
from middleware.generic.errors import GenericError, GenericProtocolError
from middleware.generic.pipeline import PipelineResult, ResultsQueueHook, run_bounded_pipeline
from middleware.generic.protocol import xml as _register_xml_protocol
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.errors import HarvesterError, RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.harvester.plugin_base import HarvestedArc
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_config import ParserConfig
from middleware.payload.linked_data_mapper import (
    LinkedDataMapper,
    MappingContext,
    register_builtins as _register_builtin_mappers,
)
from middleware.payload.mapper_config import MapperConfig, MapperType

_ = (_register_html_jsonld_parser, _register_xml_protocol, _register_builtin_mappers)

logger = logging.getLogger(__name__)


class GenericPlugin:
    """Stateful generic plugin (structurally satisfies ``Plugin``)."""

    def __init__(self, config: Config, mapper_config: MapperConfig, parser_config: ParserConfig) -> None:
        """Initialize with plugin + repository mapper/parser configuration."""
        self._config = config
        self._mapper: LinkedDataMapper = self.create_mapper(config, mapper_config)
        self._parser_cls: type[PayloadParser] = self.create_parser_class(parser_config)
        if self._parser_cls.produces != self._mapper.accepts:
            raise ValueError(
                f"parser {parser_config.type} produces {self._parser_cls.produces!r}, "
                f"but mapper accepts {self._mapper.accepts!r}"
            )

    @staticmethod
    def create_protocol(config: Config, client: NiceHttpClient) -> Protocol:
        """Create the Protocol implementation for the configured protocol type."""
        try:
            protocol_cls = Protocol.registry[config.protocol_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported protocol type: {config.protocol_type}") from exc
        return protocol_cls(config, client)

    @staticmethod
    def create_parser_class(parser_config: ParserConfig) -> type[PayloadParser]:
        """Resolve the PayloadParser implementation for the configured parser type."""
        try:
            return PayloadParser.registry[parser_config.type]
        except KeyError as exc:
            raise ValueError(f"Unsupported parser type: {parser_config.type}") from exc

    @staticmethod
    def create_mapper(config: Config, mapper_config: MapperConfig) -> LinkedDataMapper:
        """Create the mapper from repository ``mapper`` config (shared registry)."""
        try:
            mapper_cls = LinkedDataMapper.registered_class(mapper_config.type)
        except KeyError as exc:
            raise ValueError(f"Unsupported mapper type: {mapper_config.type}") from exc

        fallback = config.effective_resource_base_url if mapper_config.type == MapperType.regal_general else None
        return mapper_cls.from_config(mapper_config, resource_base_url=fallback)

    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count from the Protocol when available."""
        async with NiceHttpClient(self._config.http) as nice_http:
            protocol = self.create_protocol(self._config, client=nice_http)
            try:
                return await protocol.get_expected_count()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to determine expected dataset count for protocol %s (%s): %s",
                    self._config.protocol_type,
                    self._config.sitemap_url,
                    exc,
                )
                return None

    async def _process_result(
        self,
        discovery_result: DiscoveryResult,
        nice_http: NiceHttpClient,
    ) -> list[HarvestedArc | RecordProcessingError | SkippedRecord]:
        source_url: str | None = None
        harvest_source_id: str | None = None
        if isinstance(discovery_result, UrlDiscoveryResult):
            source_url = discovery_result.url
            harvest_source_id = discovery_result.harvest_source_id

        parser = self._parser_cls()
        try:
            payload = await parser.parse(discovery_result, client=nice_http, config=self._config)
        except (ParserError, GenericError, RuntimeError, ValueError, OSError) as exc:
            return [
                RecordProcessingError(
                    (f"Failed to parse {type(discovery_result).__name__} {discovery_result.identifier}: {exc}"),
                    discovery_result.identifier,
                    exc,
                    url=source_url,
                )
            ]

        if payload.kind != self._mapper.accepts:
            return [
                RecordProcessingError(
                    (
                        f"Payload kind {payload.kind!r} incompatible with mapper "
                        f"accepts {self._mapper.accepts!r} for {payload.identifier}"
                    ),
                    payload.identifier,
                    url=source_url,
                )
            ]

        try:
            mapping_context = MappingContext(
                source_url=source_url,
                harvest_source_id=harvest_source_id,
            )
            harvested_items = await asyncio.to_thread(
                lambda: list(self._mapper.map(payload, mapping_context)),
            )
            return [replace(harvested, source_url=source_url) for harvested in harvested_items]
        except (GenericError, RuntimeError, ValueError, OSError) as exc:
            return [
                RecordProcessingError(
                    f"Failed to map payload {payload.identifier}: {exc}",
                    payload.identifier,
                    exc,
                    url=source_url,
                )
            ]

    @staticmethod
    def _processing_failure(
        discovery_result: DiscoveryResult,
        exc: Exception,
    ) -> list[HarvestedArc | RecordProcessingError | SkippedRecord]:
        """Wrap an unexpected process failure as a record-level error."""
        url = discovery_result.identifier if isinstance(discovery_result, UrlDiscoveryResult) else None
        return [
            RecordProcessingError(
                f"Failed to process {type(discovery_result).__name__} {discovery_result.identifier}: {exc}",
                discovery_result.identifier,
                exc,
                url=url,
            )
        ]

    def _harvester_error_from_discovery_failure(self, exc: BaseException) -> HarvesterError:
        """Map a discovery-stream failure to a repository-level harvester error."""
        if isinstance(exc, HarvesterError):
            return exc
        return GenericProtocolError(f"Protocol discovery failed for {self._config.sitemap_url}: {exc}")

    async def _run_with_task_group(
        self,
        protocol: Protocol,
        nice_http: NiceHttpClient,
        worker_tasks: int,
        *,
        on_results_queue: ResultsQueueHook | None = None,
    ) -> AsyncGenerator[PipelineResult, None]:
        """Run the bounded pipeline for ``protocol`` and yield outcomes."""

        async def process(
            discovery_result: DiscoveryResult,
        ) -> list[HarvestedArc | RecordProcessingError | SkippedRecord]:
            try:
                return await self._process_result(discovery_result, nice_http)
            except (ParserError, RuntimeError, ValueError, OSError, httpx.HTTPError, GenericError) as exc:
                return self._processing_failure(discovery_result, exc)

        async for item in run_bounded_pipeline(
            discover=protocol.discover(),
            process=process,
            on_discovery_error=self._harvester_error_from_discovery_failure,
            worker_tasks=worker_tasks,
            on_results_queue=on_results_queue,
        ):
            yield item

    async def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
        """Run the plugin and yield harvested ARCs, errors, or skips."""
        async with NiceHttpClient(self._config.http) as nice_http:
            protocol = self.create_protocol(self._config, client=nice_http)
            worker_tasks = self._config.effective_worker_tasks
            async for item in self._run_with_task_group(protocol, nice_http, worker_tasks):
                yield item


# Re-export enums for tests / registration checks.
__all__ = ["GenericPlugin", "ProtocolType"]
