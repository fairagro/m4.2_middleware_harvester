"""Inline JSON-LD PayloadParser implementation."""

from __future__ import annotations

import asyncio
import json
from typing import Any, ClassVar, override

from rdflib import Graph

from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, JsonLdDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload


@PayloadParser.register(ParserType.jsonld)
class JsonLdParser(PayloadParser):
    """Parse an inline JSON-LD payload from a discovery unit into an ``rdf_graph`` payload.

    Vocabulary-agnostic (DCAT-AP, Schema.org, …): no ``@context`` allowlist is
    applied. Remote context references (string ``@context`` / ``@import``) are
    rejected so parsing never triggers network retrieval.
    """

    produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

    @override
    async def parse(
        self,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: object,
    ) -> ParsedPayload:
        """Parse inline JSON-LD without requiring an HTTP client."""
        _ = client
        if not isinstance(discovery_result, JsonLdDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")
        if not discovery_result.payload:
            raise ParserError(f"Missing JSON-LD payload for {discovery_result.identifier}")
        if _has_remote_context(discovery_result.payload):
            raise ParserError(f"Remote JSON-LD @context is not supported for {discovery_result.identifier}")

        data = json.dumps(discovery_result.payload)
        threshold = int(getattr(config, "jsonld_parse_threshold_bytes", 65536))
        if len(data.encode("utf-8")) > threshold:
            graph = await asyncio.to_thread(self._parse, data, discovery_result.identifier)
        else:
            graph = self._parse(data, discovery_result.identifier)
        if len(graph) == 0:
            raise ParserError(f"JSON-LD produced an empty graph for {discovery_result.identifier}")
        return ParsedPayload(kind=PayloadKind.rdf_graph, value=graph, identifier=discovery_result.identifier)

    @staticmethod
    def _parse(data: str, identifier: str) -> Graph:
        graph = Graph()
        try:
            graph.parse(data=data, format="json-ld")
        except Exception as exc:  # noqa: BLE001
            raise ParserError(f"Failed to parse JSON-LD for {identifier}: {exc}") from exc
        return graph


def _has_remote_context(value: Any) -> bool:
    """Return True if any ``@context`` / ``@import`` in ``value`` references a remote document."""
    if isinstance(value, list):
        return any(_has_remote_context(item) for item in value)
    if not isinstance(value, dict):
        return False
    for key, item in value.items():
        if key in {"@context", "@import"} and _references_document(item):
            return True
        if _has_remote_context(item):
            return True
    return False


def _references_document(context: Any) -> bool:
    if isinstance(context, str):
        return True
    if isinstance(context, list):
        return any(_references_document(item) for item in context)
    return False
