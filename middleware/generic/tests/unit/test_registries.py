"""Unit tests for Protocol / PayloadParser registries."""

from __future__ import annotations

from typing import ClassVar, override

# Ensure builtins are registered.
import middleware.generic.parser.html_jsonld  # noqa: F401
import middleware.generic.protocol.xml  # noqa: F401
from middleware.generic.config import ParserType, ProtocolType
from middleware.generic.discovery import DiscoveryResult
from middleware.generic.parser.parser import PayloadParser
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload


def test_xml_protocol_registered() -> None:
    assert ProtocolType.xml in Protocol.registry
    assert issubclass(Protocol.registry[ProtocolType.xml], Protocol)


def test_html_jsonld_parser_registered_and_produces_rdf() -> None:
    parser_cls = PayloadParser.registry[ParserType.html_jsonld]
    assert parser_cls.produces == PayloadKind.rdf_graph


def test_fake_parser_produces() -> None:
    class _FakeParser(PayloadParser):
        produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

        @override
        async def parse(
            self,
            discovery_result: DiscoveryResult,
            client: NiceHttpClient | None,
            config: object,
        ) -> ParsedPayload:
            _ = client, config
            return ParsedPayload(kind=PayloadKind.rdf_graph, value=object(), identifier=discovery_result.identifier)

    assert _FakeParser.produces == PayloadKind.rdf_graph
