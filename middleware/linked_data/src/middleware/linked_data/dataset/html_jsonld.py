"""HTML JSON-LD dataset — shim over ``middleware.generic`` HtmlJsonLdParser."""

from __future__ import annotations

from rdflib import Graph

from middleware.generic.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.generic.errors import GenericParserError
from middleware.generic.parser.html_jsonld import HtmlJsonLdParser
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import Config, DatasetType
from middleware.linked_data.dataset.dataset import Dataset
from middleware.linked_data.errors import LinkedDataDatasetError


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

    async def to_graph(self) -> Graph:
        """Fetch the HTML page and parse all embedded JSON-LD blocks into an rdflib.Graph."""
        parser = HtmlJsonLdParser()
        try:
            payload = await parser.parse(
                UrlDiscoveryResult(self._url),
                client=self._client,
                config=self._config,
            )
        except GenericParserError as exc:
            raise LinkedDataDatasetError(str(exc)) from exc
        if not isinstance(payload.value, Graph):
            raise LinkedDataDatasetError(f"Expected RDF Graph from HtmlJsonLdParser, got {type(payload.value)!r}")
        return payload.value
