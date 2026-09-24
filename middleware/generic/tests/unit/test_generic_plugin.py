"""Unit tests for GenericPlugin orchestration helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import ClassVar, override
from unittest.mock import AsyncMock, MagicMock

import pytest
from rdflib import Graph

import middleware.generic.plugin as plugin_mod
import middleware.generic.protocol.xml as _register_xml
import middleware.parsing.register_builtin_parsers as _register_parsers
import middleware.payload.linked_data_mapper.register_builtins as _register_builtin_mappers
from middleware.generic.config import Config, ProtocolType
from middleware.generic.plugin import GenericPlugin
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.harvester.plugin_base import HarvestedArc
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_config import ParserConfig
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.parsed_payload import ParsedPayload

_ = (_register_parsers, _register_xml, _register_builtin_mappers)


def _config(**overrides: object) -> Config:
    raw: dict[str, object] = {
        "protocol_type": ProtocolType.xml,
        "sitemap_url": "https://example.org/sitemap.xml",
    }
    raw.update(overrides)
    return Config.model_validate(raw)


def _parser_config() -> ParserConfig:
    return ParserConfig(type=ParserType.html_jsonld)


def _patch_nice_http(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    monkeypatch.setattr(plugin_mod, "NiceHttpClient", MagicMock(return_value=mock_client))
    return mock_client


@pytest.mark.asyncio
async def test_get_expected_datasets_soft_none_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BoomProtocol(Protocol):
        @override
        async def get_expected_count(self) -> int | None:
            raise RuntimeError("boom")

        @override
        async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult, None]:
            _ = client
            if False:  # pragma: no cover  # noqa: make this an async generator
                yield UrlDiscoveryResult("")

    plugin = GenericPlugin(_config(), MapperConfig(type=MapperType.schema_org_general), _parser_config())
    plugin.create_protocol = MagicMock(return_value=_BoomProtocol(_config(), MagicMock()))  # type: ignore[method-assign]
    _patch_nice_http(monkeypatch)

    assert await plugin.get_expected_datasets() is None


@pytest.mark.asyncio
async def test_process_result_kind_mismatch_yields_error() -> None:
    class _StubParser(PayloadParser):
        produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

        @override
        async def parse(
            self,
            discovery_result: DiscoveryResult,
            client: NiceHttpClient | None,
            config: object,
        ) -> ParsedPayload:
            _ = client, config
            return ParsedPayload(kind=PayloadKind.rdf_graph, value=Graph(), identifier=discovery_result.identifier)

    plugin = GenericPlugin(_config(), MapperConfig(type=MapperType.schema_org_general), _parser_config())
    # Runtime kind check: mapper accepts differs from the payload kind (rdf_graph).
    stub_mapper = MagicMock()
    stub_mapper.accepts = object()
    plugin._mapper = stub_mapper  # noqa: SLF001
    plugin._parser_cls = _StubParser  # noqa: SLF001

    outcomes = await plugin._process_result(UrlDiscoveryResult("https://example.org/a"), MagicMock())  # noqa: SLF001
    assert len(outcomes) == 1
    assert isinstance(outcomes[0], RecordProcessingError)
    assert "incompatible" in str(outcomes[0])


@pytest.mark.asyncio
async def test_run_yields_harvested_arc_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class _OkProtocol(Protocol):
        @override
        async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult, None]:
            _ = client
            yield UrlDiscoveryResult("https://example.org/dataset/1")

    class _OkParser(PayloadParser):
        produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

        @override
        async def parse(
            self,
            discovery_result: DiscoveryResult,
            client: NiceHttpClient | None,
            config: object,
        ) -> ParsedPayload:
            _ = client, config
            return ParsedPayload(
                kind=PayloadKind.rdf_graph,
                value=Graph(),
                identifier=discovery_result.identifier,
            )

    stub_mapper = MagicMock()
    stub_mapper.accepts = PayloadKind.rdf_graph
    stub_mapper.map.return_value = [HarvestedArc(arc_json="mapped:arc")]

    plugin = GenericPlugin(_config(), MapperConfig(type=MapperType.schema_org_general), _parser_config())
    plugin.create_protocol = MagicMock(return_value=_OkProtocol(_config(), MagicMock()))  # type: ignore[method-assign]
    plugin._parser_cls = _OkParser  # noqa: SLF001
    plugin._mapper = stub_mapper  # noqa: SLF001
    _patch_nice_http(monkeypatch)

    results = [item async for item in plugin.run()]
    assert results == [HarvestedArc(arc_json="mapped:arc", source_url="https://example.org/dataset/1")]
    stub_mapper.map.assert_called_once()


@pytest.mark.asyncio
async def test_run_forwards_skipped_record_from_protocol(monkeypatch: pytest.MonkeyPatch) -> None:
    class _SkipProtocol:
        async def discover(self) -> AsyncGenerator[SkippedRecord, None]:  # noqa: PLR6301
            yield SkippedRecord(
                "Duplicate discovery entry skipped: https://example.org/dataset/dup",
                "https://example.org/dataset/dup",
            )

        async def get_expected_count(self) -> int | None:  # noqa: PLR6301
            return None

    plugin = GenericPlugin(_config(), MapperConfig(type=MapperType.schema_org_general), _parser_config())
    plugin.create_protocol = MagicMock(return_value=_SkipProtocol())  # type: ignore[method-assign]
    _patch_nice_http(monkeypatch)

    results = [item async for item in plugin.run()]
    assert len(results) == 1
    assert isinstance(results[0], SkippedRecord)
    assert "Duplicate discovery entry" in str(results[0])


@pytest.mark.asyncio
async def test_run_empty_discovery_exits_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    class _EmptyProtocol:
        async def discover(self) -> AsyncGenerator[DiscoveryResult, None]:  # noqa: PLR6301
            if False:  # pragma: no cover  # noqa: make this an async generator
                yield UrlDiscoveryResult("")

        async def get_expected_count(self) -> int | None:  # noqa: PLR6301
            return 0

    plugin = GenericPlugin(_config(), MapperConfig(type=MapperType.schema_org_general), _parser_config())
    plugin.create_protocol = MagicMock(return_value=_EmptyProtocol())  # type: ignore[method-assign]
    _patch_nice_http(monkeypatch)

    results = [item async for item in plugin.run()]
    assert results == []
