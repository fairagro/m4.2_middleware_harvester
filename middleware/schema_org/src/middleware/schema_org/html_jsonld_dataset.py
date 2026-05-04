"""HTML JSON-LD dataset implementation."""

from __future__ import annotations

import json
from html.parser import HTMLParser

import httpx
from rdflib import Graph

from .config import DatasetType
from .dataset import Dataset, DiscoveryResult, UrlDiscoveryResult
from .errors import SchemaOrgDatasetError


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
    def from_discovery_result(
        cls, discovery_result: DiscoveryResult, client: httpx.AsyncClient | None = None
    ) -> Dataset:
        """Construct an HtmlJsonLdDataset from a UrlDiscoveryResult.

        Raises ValueError for unsupported discovery result types or when no HTTP client is provided.
        """
        if not isinstance(discovery_result, UrlDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")

        if client is None:
            raise ValueError(
                "HtmlJsonLdDataset requires an httpx.AsyncClient. Provide the client to from_discovery_result()."
            )

        return cls(discovery_result.url, client)

    async def to_graph(self) -> Graph:
        """Fetch the HTML page and parse all embedded JSON-LD blocks into an rdflib.Graph."""
        response = await self._client.get(self._url)
        if response.is_error:
            raise SchemaOrgDatasetError(f"HTTP {response.status_code} fetching dataset URL: {self._url}")

        parser = _JsonLdScriptParser()
        parser.feed(response.text)

        if not parser.blocks:
            raise SchemaOrgDatasetError(f"No JSON-LD blocks found in HTML at: {self._url}")

        merged = Graph()
        for block in parser.blocks:
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                raise SchemaOrgDatasetError(f"Invalid JSON in JSON-LD block at {self._url}: {exc}") from exc

            block_graph = Graph()
            try:
                block_graph.parse(data=block, format="json-ld")
            except Exception as exc:  # noqa: BLE001
                raise SchemaOrgDatasetError(f"Failed to parse JSON-LD at {self._url}: {exc}") from exc

            merged += block_graph

        return merged
