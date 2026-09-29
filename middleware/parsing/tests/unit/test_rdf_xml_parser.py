"""Unit tests for XmlDiscoveryResult and RdfXmlParser."""

from __future__ import annotations

from pathlib import Path

import pytest

import middleware.parsing.register_builtin_parsers as _register_builtin_parsers
from middleware.parsing.discovery import UrlDiscoveryResult, XmlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser.rdf_xml import RdfXmlParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind

_ = _register_builtin_parsers

_FIXTURE = Path(__file__).parent / "fixtures" / "minimal_rdf_xml.xml"


def test_xml_discovery_result_carries_identifier_and_xml() -> None:
    unit = XmlDiscoveryResult(identifier="oai:example.org:1", xml="<rdf:RDF/>")
    assert unit.identifier == "oai:example.org:1"
    assert unit.xml == "<rdf:RDF/>"


def test_rdf_xml_parser_registered_and_produces_rdf() -> None:
    parser_cls = PayloadParser.registry[ParserType.rdf_xml]
    assert parser_cls is RdfXmlParser
    assert parser_cls.produces == PayloadKind.rdf_graph


@pytest.mark.asyncio
async def test_rdf_xml_parser_happy_path_without_client() -> None:
    xml = _FIXTURE.read_text(encoding="utf-8")
    payload = await RdfXmlParser().parse(
        XmlDiscoveryResult(identifier="oai:example.org:1", xml=xml),
        client=None,
        config=object(),
    )
    assert payload.kind == PayloadKind.rdf_graph
    assert payload.identifier == "oai:example.org:1"
    assert len(payload.value) > 0


@pytest.mark.asyncio
async def test_rdf_xml_parser_missing_metadata_raises() -> None:
    with pytest.raises(ParserError, match="Missing RDF/XML"):
        await RdfXmlParser().parse(
            XmlDiscoveryResult(identifier="oai:example.org:empty", xml="  "),
            client=None,
            config=object(),
        )


@pytest.mark.asyncio
async def test_rdf_xml_parser_malformed_raises() -> None:
    with pytest.raises(ParserError, match="Failed to parse RDF/XML"):
        await RdfXmlParser().parse(
            XmlDiscoveryResult(identifier="oai:example.org:bad", xml="<not-rdf>"),
            client=None,
            config=object(),
        )


@pytest.mark.asyncio
async def test_rdf_xml_parser_rejects_url_discovery() -> None:
    with pytest.raises(ValueError, match="Unsupported discovery result type"):
        await RdfXmlParser().parse(
            UrlDiscoveryResult("https://example.org/page"),
            client=None,
            config=object(),
        )
