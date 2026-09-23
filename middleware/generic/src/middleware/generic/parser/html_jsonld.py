"""HTML JSON-LD PayloadParser implementation."""

from __future__ import annotations

import asyncio
import json
import logging
from html.parser import HTMLParser
from typing import ClassVar, override

from rdflib import Graph

from middleware.generic.config import ParserType
from middleware.generic.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.generic.errors import GenericParserError
from middleware.generic.jsonld_validation import JsonLdContextError, validate_jsonld_context_data
from middleware.generic.parser.parser import PayloadParser
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload

logger = logging.getLogger(__name__)


class _JsonLdScriptParser(HTMLParser):
    """Minimal HTML parser that collects the text of every JSON-LD script block."""

    def __init__(self) -> None:
        super().__init__()
        self._in_jsonld: bool = False
        self._current_block: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and ("type", "application/ld+json") in attrs:
            self._in_jsonld = True
            self._current_block = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            self.blocks.append("".join(self._current_block))
            self._current_block = []

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self._current_block.append(data)


@PayloadParser.register(ParserType.html_jsonld)
class HtmlJsonLdParser(PayloadParser):
    """Fetch an HTML page and extract embedded JSON-LD into an RDF graph payload."""

    produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

    @override
    async def parse(
        self,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: object,
    ) -> ParsedPayload:
        """Fetch HTML for a URL discovery result and return an ``rdf_graph`` payload."""
        if not isinstance(discovery_result, UrlDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")
        if client is None:
            raise ValueError("HtmlJsonLdParser requires an HTTP client; client must not be None.")

        threshold = int(getattr(config, "jsonld_parse_threshold_bytes", 65536))
        graph = await self._url_to_graph(discovery_result.url, client, threshold)
        return ParsedPayload(kind=PayloadKind.rdf_graph, value=graph, identifier=discovery_result.identifier)

    async def _url_to_graph(self, url: str, client: NiceHttpClient, threshold: int) -> Graph:
        try:
            response = await client.get_with_policy(url, follow_redirects=True)
            html_text = response.text
        except Exception as exc:  # noqa: BLE001
            raise GenericParserError(f"Failed to fetch dataset URL {url}: {exc}") from exc
        return await self.graph_from_html(url, html_text, threshold)

    async def graph_from_html(self, url: str, html_text: str, threshold: int) -> Graph:
        """Parse embedded JSON-LD from already-fetched HTML into an RDF graph.

        Used by callers (e.g. ``HtmlJsonLdDataset``) that cache the HTML for
        page-title hints and must avoid a second HTTP fetch.
        """
        parser = _JsonLdScriptParser()
        parser.feed(html_text)
        if not parser.blocks:
            raise GenericParserError(f"No JSON-LD blocks found in HTML at: {url}")

        normalized_blocks: list[str] = []
        for block in parser.blocks:
            try:
                parsed = json.loads(block, strict=False)
            except json.JSONDecodeError as exc:
                raise GenericParserError(f"Invalid JSON in JSON-LD block at {url}: {exc}\nBlock:\n{block}") from exc
            try:
                validate_jsonld_context_data(parsed)
            except JsonLdContextError as exc:
                raise GenericParserError(f"Unsupported @context in JSON-LD block at {url}: {exc}") from exc
            normalized_blocks.append(json.dumps(parsed))

        merged = Graph()
        for block in normalized_blocks:
            if len(block.encode("utf-8")) > threshold:
                block_graph = await asyncio.to_thread(self._parse_jsonld_block, block, url)
            else:
                block_graph = self._parse_jsonld_block(block, url)
            merged += block_graph
        return merged

    @staticmethod
    def _parse_jsonld_block(block: str, url: str) -> Graph:
        graph = Graph()
        try:
            graph.parse(data=block, format="json-ld")
        except Exception as exc:  # noqa: BLE001
            raise GenericParserError(f"Failed to parse JSON-LD at {url}: {exc}\nBlock:\n{block}") from exc
        return graph
