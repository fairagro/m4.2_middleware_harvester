"""HTML JSON-LD dataset — shim over ``middleware.generic`` HtmlJsonLdParser."""

from __future__ import annotations

from html.parser import HTMLParser

from rdflib import Graph

from middleware.generic.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.generic.errors import GenericParserError
from middleware.generic.parser.html_jsonld import HtmlJsonLdParser
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import Config, DatasetType
from middleware.linked_data.dataset.dataset import Dataset
from middleware.linked_data.errors import LinkedDataDatasetError


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

    async def _ensure_html(self) -> str:
        """Fetch the page once and cache the HTML body."""
        if self._html_text is None:
            self._html_text = await self._fetch_html(self._url, self._client)
        return self._html_text

    async def to_graph(self) -> Graph:
        """Fetch the HTML page and parse all embedded JSON-LD blocks into an rdflib.Graph."""
        html_text = await self._ensure_html()
        parser = HtmlJsonLdParser()
        try:
            return await parser.graph_from_html(
                self._url,
                html_text,
                self._jsonld_parse_threshold_bytes,
            )
        except GenericParserError as exc:
            raise LinkedDataDatasetError(str(exc)) from exc

    async def title_hint(self) -> str | None:
        """``citation_title`` meta content, else ``<title>`` text, from the fetched page."""
        html_text = await self._ensure_html()
        return _extract_title_hint(html_text)

    def title_hint_from_cache(self) -> str | None:
        """``title_hint()`` result using only the HTML already fetched by ``to_graph()``.

        Returns ``None`` (no I/O, no parse) when nothing has been fetched yet.
        Lets callers pass this as a lazy ``MappingContext.html_title`` provider
        without paying for a second ``HTMLParser`` pass unless it's invoked.
        """
        return _extract_title_hint(self._html_text) if self._html_text is not None else None
