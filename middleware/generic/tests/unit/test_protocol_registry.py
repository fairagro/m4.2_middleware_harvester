"""Unit tests for Protocol registry (parsers live in middleware.parsing)."""

from __future__ import annotations

import middleware.generic.protocol.xml as _register_xml
import middleware.parsing.register_builtin_parsers as _register_parsers
from middleware.generic.config import ProtocolType
from middleware.generic.protocol.protocol import Protocol
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind

_ = (_register_xml, _register_parsers)


def test_xml_protocol_registered() -> None:
    assert ProtocolType.xml in Protocol.registry
    assert issubclass(Protocol.registry[ProtocolType.xml], Protocol)


def test_html_jsonld_parser_registered_via_parsing() -> None:
    parser_cls = PayloadParser.registry[ParserType.html_jsonld]
    assert parser_cls.produces == PayloadKind.rdf_graph
