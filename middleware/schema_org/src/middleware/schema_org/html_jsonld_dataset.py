"""HTML JSON-LD dataset implementation."""

from __future__ import annotations

import json
from html.parser import HTMLParser

import httpx
from rdflib import Graph

from .config import DatasetType
from .dataset import Dataset, DiscoveryResult, UrlDiscoveryResult


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


@Dataset.register(DatasetType.html_jsonld)
class HtmlJsonLdDataset(Dataset):
    """Dataset that fetches an HTML page and extracts embedded JSON-LD markup."""

    def __init__(self, url: str, client: httpx.AsyncClient) -> None:
        """Initialize with the page URL and the shared HTTP client."""
        self._url = url
        self._client = client

    @property
    def identifier(self) -> str:
        """Return the page URL as the stable dataset identifier."""
        return self._url

    @classmethod
    def from_discovery_result(cls, discovery_result: DiscoveryResult) -> Dataset:
        """Construct an HtmlJsonLdDataset from a UrlDiscoveryResult.

        Raises ValueError for non-URL discovery results.
        The caller must supply an httpx.AsyncClient separately via __init__
        because Dataset.from_discovery_result() does not carry infrastructure.
        Use HtmlJsonLdDataset(url, client) directly when a client is available.
        """
        if isinstance(discovery_result, UrlDiscoveryResult):
            raise ValueError(
                "HtmlJsonLdDataset requires an httpx.AsyncClient. Use HtmlJsonLdDataset(url, client) directly."
            )
        raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")

    async def to_graph(self) -> Graph:
        """Fetch the HTML page and parse all embedded JSON-LD blocks into an rdflib.Graph."""
        response = await self._client.get(self._url)
        if response.is_error:
            raise ValueError(f"HTTP {response.status_code} fetching dataset URL: {self._url}")

        parser = _JsonLdScriptParser()
        parser.feed(response.text)

        if not parser.blocks:
            raise ValueError(f"No JSON-LD blocks found in HTML at: {self._url}")

        merged = Graph()
        for block in parser.blocks:
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in JSON-LD block at {self._url}: {exc}") from exc
            block_graph = Graph()
            block_graph.parse(data=block, format="json-ld")
            merged += block_graph

        return merged
