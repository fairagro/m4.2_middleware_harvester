"""HTML JSON-LD dataset implementation."""

from __future__ import annotations

import asyncio
import json
import logging
from html.parser import HTMLParser

from rdflib import Graph

from middleware.harvester.nice_http_client import NiceHttpClient

from ..config import Config, DatasetType
from ..errors import LinkedDataDatasetError
from ..jsonld_validation import JsonLdContextError, validate_jsonld_context_data
from .dataset import Dataset, DiscoveryResult, UrlDiscoveryResult

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


class _TitleHintParser(HTMLParser):
    """Collects ``<meta name="citation_title">`` content and ``<title>`` text."""

    def __init__(self) -> None:
        super().__init__()
        self.citation_title: str | None = None
        self.title: str | None = None
        self._in_title: bool = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
            self._title_parts = []
            return
        if tag == "meta" and self.citation_title is None:
            attr_map = dict(attrs)
            if (attr_map.get("name") or "").strip().lower() == "citation_title":
                content = (attr_map.get("content") or "").strip()
                if content:
                    self.citation_title = content

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = "".join(self._title_parts).strip() or None

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)


def _extract_title_hint(html: str) -> str | None:
    """Best-effort page title: ``citation_title`` meta content, else ``<title>``."""
    parser = _TitleHintParser()
    parser.feed(html)
    return parser.citation_title or parser.title


@Dataset.register(DatasetType.html_jsonld)
class HtmlJsonLdDataset(Dataset):
    """Dataset that fetches an HTML page and extracts embedded JSON-LD markup."""

    def __init__(
        self,
        url: str,
        client: NiceHttpClient,
        config: Config,
    ) -> None:
        """Initialize with the page URL, HTTP client, and configuration."""
        self._url = url
        self._client = client
        self._config = config
        self._jsonld_parse_threshold_bytes = config.jsonld_parse_threshold_bytes
        self._jsonld_blocks: list[str] | None = None
        self._html_text: str | None = None

    @property
    def identifier(self) -> str:
        """The page URL as the stable dataset identifier."""
        return self._url

    @classmethod
    def from_discovery_result(
        cls,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: Config,
    ) -> Dataset:
        """Construct an HtmlJsonLdDataset from a UrlDiscoveryResult."""
        if not isinstance(discovery_result, UrlDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")
        if client is None:
            raise ValueError("HtmlJsonLdDataset requires an HTTP client; client must not be None.")

        return cls(
            discovery_result.url,
            client,
            config,
        )

    async def _ensure_jsonld_blocks(self) -> list[str]:
        """Fetch HTML once and return normalized JSON-LD script block strings."""
        if self._jsonld_blocks is not None:
            return self._jsonld_blocks

        html_text = await self._fetch_html(self._url, self._client)
        self._html_text = html_text
        parser = _JsonLdScriptParser()
        parser.feed(html_text)

        if not parser.blocks:
            raise LinkedDataDatasetError(f"No JSON-LD blocks found in HTML at: {self._url}")

        normalized_blocks: list[str] = []
        for block in parser.blocks:
            try:
                parsed = json.loads(block, strict=False)
            except json.JSONDecodeError as exc:
                raise LinkedDataDatasetError(
                    f"Invalid JSON in JSON-LD block at {self._url}: {exc}\nBlock:\n{block}"
                ) from exc
            try:
                validate_jsonld_context_data(parsed)
            except JsonLdContextError as exc:
                raise LinkedDataDatasetError(f"Unsupported @context in JSON-LD block at {self._url}: {exc}") from exc
            normalized_blocks.append(json.dumps(parsed))

        self._jsonld_blocks = normalized_blocks
        return normalized_blocks

    async def to_graph(self) -> Graph:
        """Fetch the HTML page and parse all embedded JSON-LD blocks into an rdflib.Graph."""
        blocks = await self._ensure_jsonld_blocks()
        merged = Graph()

        for block in blocks:
            if len(block.encode("utf-8")) > self._jsonld_parse_threshold_bytes:
                block_graph = await asyncio.to_thread(self._parse_jsonld_block, block)
            else:
                block_graph = Graph()
                try:
                    block_graph.parse(data=block, format="json-ld")
                except Exception as exc:  # noqa: BLE001
                    raise LinkedDataDatasetError(
                        f"Failed to parse JSON-LD at {self._url}: {exc}\nBlock:\n{block}"
                    ) from exc

            merged += block_graph

        return merged

    async def title_hint(self) -> str | None:
        """``citation_title`` meta content, else ``<title>`` text, from the fetched page."""
        if self._html_text is None:
            self._html_text = await self._fetch_html(self._url, self._client)
        return _extract_title_hint(self._html_text)

    def _parse_jsonld_block(self, block: str) -> Graph:
        graph = Graph()
        try:
            graph.parse(data=block, format="json-ld")
        except Exception as exc:  # noqa: BLE001
            raise LinkedDataDatasetError(f"Failed to parse JSON-LD at {self._url}: {exc}\nBlock:\n{block}") from exc
        return graph
