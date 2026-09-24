"""Inline RDF/XML PayloadParser implementation."""

from __future__ import annotations

from typing import ClassVar, override

from rdflib import Graph

from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, XmlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload


@PayloadParser.register(ParserType.rdf_xml)
class RdfXmlParser(PayloadParser):
    """Parse inline RDF/XML from a discovery unit into an ``rdf_graph`` payload."""

    produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

    @override
    async def parse(
        self,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: object,
    ) -> ParsedPayload:
        """Parse inline RDF/XML without requiring an HTTP client."""
        _ = client, config
        if not isinstance(discovery_result, XmlDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")
        xml = discovery_result.xml.strip() if discovery_result.xml else ""
        if not xml:
            raise ParserError(f"Missing RDF/XML metadata for {discovery_result.identifier}")

        graph = Graph()
        try:
            graph.parse(data=xml, format="xml")
        except Exception as exc:  # noqa: BLE001
            raise ParserError(f"Failed to parse RDF/XML for {discovery_result.identifier}: {exc}") from exc
        if len(graph) == 0:
            raise ParserError(f"RDF/XML produced an empty graph for {discovery_result.identifier}")
        return ParsedPayload(kind=PayloadKind.rdf_graph, value=graph, identifier=discovery_result.identifier)
