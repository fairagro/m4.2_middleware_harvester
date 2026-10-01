"""Inline JSON-LD PayloadParser implementation."""

from __future__ import annotations

import asyncio
import json
from typing import ClassVar, cast, override

from rdflib import Graph

from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, JsonLdDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.jsonld_context_loader import materialize_payload_contexts
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload
from middleware.shared.json_types import JsonObject


@PayloadParser.register(ParserType.jsonld)
class JsonLdParser(PayloadParser):
    """Parse an inline JSON-LD payload from a discovery unit into an ``rdf_graph`` payload.

    Vocabulary-agnostic (DCAT-AP, Schema.org, …). Remote ``@context`` IRIs are resolved
    through the shared process-lifetime context cache. Prefer
    ``parser.allowed_context_url`` (exact match); when unset, remotes are still
    fetched (``ParserConfig`` warns at load) for backward compatibility.
    """

    produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

    @override
    async def parse(
        self,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: object,
    ) -> ParsedPayload:
        """Parse inline JSON-LD; HTTP client required only when resolving a remote context."""
        if not isinstance(discovery_result, JsonLdDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")
        if not discovery_result.payload:
            raise ParserError(f"Missing JSON-LD payload for {discovery_result.identifier}")

        allowed = getattr(config, "allowed_context_url", None)
        document = await materialize_payload_contexts(
            cast(JsonObject, discovery_result.payload),
            allowed_context_url=allowed if isinstance(allowed, str) else None,
            client=client,
        )

        data = json.dumps(document)
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
