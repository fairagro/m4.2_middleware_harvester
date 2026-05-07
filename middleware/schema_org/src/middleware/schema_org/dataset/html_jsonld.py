"""HTML JSON-LD dataset implementation."""

from __future__ import annotations

import asyncio
import json
import logging
from html.parser import HTMLParser

from rdflib import Graph

from middleware.harvester.nice_http_client import NiceHttpClient

from ..config import Config, DatasetType
from ..errors import SchemaOrgDatasetError
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

    @property
    def identifier(self) -> str:
        """Return the page URL as the stable dataset identifier."""
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

    async def to_graph(self) -> Graph:
        """Fetch the HTML page and parse all embedded JSON-LD blocks into an rdflib.Graph."""
        html_text = await self._fetch_html(self._url, self._client)

        parser = _JsonLdScriptParser()
        parser.feed(html_text)

        if not parser.blocks:
            raise SchemaOrgDatasetError(f"No JSON-LD blocks found in HTML at: {self._url}")

        merged = Graph()

        for block in parser.blocks:
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                raise SchemaOrgDatasetError(
                    f"Invalid JSON in JSON-LD block at {self._url}: {exc}\nBlock:\n{block}"
                ) from exc

            if len(block.encode("utf-8")) > self._jsonld_parse_threshold_bytes:
                block_graph = await asyncio.to_thread(self._parse_jsonld_block, block)
            else:
                block_graph = Graph()
                try:
                    block_graph.parse(data=block, format="json-ld")
                except Exception as exc:  # noqa: BLE001
                    raise SchemaOrgDatasetError(
                        f"Failed to parse JSON-LD at {self._url}: {exc}\nBlock:\n{block}"
                    ) from exc

            merged += block_graph

        return merged

    def _parse_jsonld_block(self, block: str) -> Graph:
        graph = Graph()
        try:
            graph.parse(data=block, format="json-ld")
        except Exception as exc:  # noqa: BLE001
            raise SchemaOrgDatasetError(f"Failed to parse JSON-LD at {self._url}: {exc}\nBlock:\n{block}") from exc
        return graph
