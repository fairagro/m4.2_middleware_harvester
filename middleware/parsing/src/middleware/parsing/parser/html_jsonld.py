"""HTML JSON-LD PayloadParser implementation."""

from __future__ import annotations

import asyncio
import json
import logging
from html.parser import HTMLParser
from typing import ClassVar, cast, override

from rdflib import Graph

from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.jsonld_context_loader import materialize_payload_contexts
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload
from middleware.shared.json_types import JsonObject, JsonValue

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
        allowed = getattr(config, "allowed_context_url", None)
        allowed_url: list[str] | None = allowed if isinstance(allowed, list) else None
        graph = await self._url_to_graph(discovery_result.url, client, threshold, allowed_url)
        return ParsedPayload(kind=PayloadKind.rdf_graph, value=graph, identifier=discovery_result.identifier)

    async def _url_to_graph(
        self,
        url: str,
        client: NiceHttpClient,
        threshold: int,
        allowed_context_url: list[str] | None,
    ) -> Graph:
        try:
            response = await client.get_with_policy(url, follow_redirects=True)
            html_text = response.text
        except Exception as exc:  # noqa: BLE001
            raise ParserError(f"Failed to fetch dataset URL {url}: {exc}") from exc
        return await self.graph_from_html(
            url,
            html_text,
            threshold,
            client=client,
            allowed_context_url=allowed_context_url,
        )

    async def graph_from_html(
        self,
        url: str,
        html_text: str,
        threshold: int,
        *,
        client: NiceHttpClient | None = None,
        allowed_context_url: list[str] | None = None,
    ) -> Graph:
        """Parse embedded JSON-LD from already-fetched HTML into an RDF graph.

        Used by callers (e.g. ``HtmlJsonLdDataset``) that cache the HTML for
        page-title hints and must avoid a second HTTP fetch of the page.
        """
        parser = _JsonLdScriptParser()
        parser.feed(html_text)
        if not parser.blocks:
            raise ParserError(f"No JSON-LD blocks found in HTML at: {url}")

        normalized_blocks: list[str] = []
        for block in parser.blocks:
            normalized_blocks.append(
                await self._normalize_jsonld_block(block, url, client=client, allowed_context_url=allowed_context_url)
            )

        merged = Graph()
        for block in normalized_blocks:
            if len(block.encode("utf-8")) > threshold:
                block_graph = await asyncio.to_thread(self._parse_jsonld_block, block, url)
            else:
                block_graph = self._parse_jsonld_block(block, url)
            merged += block_graph
        return merged

    @staticmethod
    async def _normalize_jsonld_block(
        block: str,
        url: str,
        *,
        client: NiceHttpClient | None,
        allowed_context_url: list[str] | None,
    ) -> str:
        try:
            parsed = json.loads(block, strict=False)
        except json.JSONDecodeError as exc:
            raise ParserError(f"Invalid JSON in JSON-LD block at {url}: {exc}\nBlock:\n{block}") from exc
        if isinstance(parsed, list):
            if not parsed:
                raise ParserError(f"Empty JSON-LD array in block at {url}")
            items: list[JsonValue] = []
            for index, item in enumerate(parsed):
                if not isinstance(item, dict):
                    raise ParserError(
                        f"JSON-LD array item {index} at {url} must be a JSON object, got {type(item).__name__}"
                    )
                items.append(
                    await materialize_payload_contexts(
                        cast(JsonObject, item),
                        allowed_context_url=allowed_context_url,
                        client=client,
                    )
                )
            return json.dumps(items)
        if isinstance(parsed, dict):
            materialized = await materialize_payload_contexts(
                cast(JsonObject, parsed),
                allowed_context_url=allowed_context_url,
                client=client,
            )
            return json.dumps(materialized)
        raise ParserError(f"JSON-LD block at {url} must be a JSON object or array, got {type(parsed).__name__}")

    @staticmethod
    def _parse_jsonld_block(block: str, url: str) -> Graph:
        graph = Graph()
        try:
            graph.parse(data=block, format="json-ld")
        except Exception as exc:  # noqa: BLE001
            raise ParserError(f"Failed to parse JSON-LD at {url}: {exc}\nBlock:\n{block}") from exc
        return graph
