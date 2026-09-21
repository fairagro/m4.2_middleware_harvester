"""Unit tests for GenericPlugin orchestration helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import ClassVar, override
from unittest.mock import AsyncMock, MagicMock

import pytest
from rdflib import Graph

import middleware.generic.parser.html_jsonld  # noqa: F401
import middleware.generic.plugin as plugin_mod
import middleware.generic.protocol.xml  # noqa: F401
import middleware.payload.linked_data_mapper.register_builtins  # noqa: F401
from middleware.generic.config import Config, ParserType, ProtocolType
from middleware.generic.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.generic.parser.parser import PayloadParser
from middleware.generic.plugin import GenericPlugin
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.parsed_payload import ParsedPayload


def _config(**overrides: object) -> Config:
    raw: dict[str, object] = {
        "protocol_type": ProtocolType.xml,
        "parser_type": ParserType.html_jsonld,
        "sitemap_url": "https://example.org/sitemap.xml",
    }
    raw.update(overrides)
    return Config.model_validate(raw)


@pytest.mark.asyncio
async def test_get_expected_datasets_soft_none_on_failure() -> None:
    class _BoomProtocol(Protocol):
        @override
        async def get_expected_count(self) -> int | None:
            raise RuntimeError("boom")

        @override
        async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult, None]:
            _ = client
            if False:  # pragma: no cover
                yield UrlDiscoveryResult("")

    plugin = GenericPlugin(_config(), MapperConfig(type=MapperType.schema_org_general))
    plugin.create_protocol = MagicMock(return_value=_BoomProtocol(_config(), MagicMock()))  # type: ignore[method-assign]
    # NiceHttpClient context manager
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    original = plugin_mod.NiceHttpClient
    plugin_mod.NiceHttpClient = MagicMock(return_value=mock_client)  # type: ignore[misc,assignment]
    try:
        assert await plugin.get_expected_datasets() is None
    finally:
        plugin_mod.NiceHttpClient = original  # type: ignore[misc]


@pytest.mark.asyncio
async def test_process_result_kind_mismatch_yields_error() -> None:
    class _WrongKindParser(PayloadParser):
        produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

        @override
        async def parse(
            self,
            discovery_result: DiscoveryResult,
            client: NiceHttpClient | None,
            config: object,
        ) -> ParsedPayload:
            _ = client, config
            # Deliberately wrong kind to hit the runtime check (bypassing ClassVar).
            return ParsedPayload(kind=PayloadKind.rdf_graph, value=Graph(), identifier=discovery_result.identifier)

    plugin = GenericPlugin(_config(), MapperConfig(type=MapperType.schema_org_general))
    # Force mapper accepts to differ by swapping mapper.accepts via a stub.
    stub_mapper = MagicMock()
    stub_mapper.accepts = object()  # not rdf_graph
    plugin._mapper = stub_mapper  # noqa: SLF001
    plugin._parser_cls = _WrongKindParser  # noqa: SLF001

    outcomes = await plugin._process_result(UrlDiscoveryResult("https://example.org/a"), MagicMock())  # noqa: SLF001
    assert len(outcomes) == 1
    assert isinstance(outcomes[0], RecordProcessingError)
    assert "incompatible" in str(outcomes[0])
