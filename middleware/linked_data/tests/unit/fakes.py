"""Shared fake test helpers for linked_data unit tests."""

import asyncio
from collections.abc import AsyncGenerator

import httpx
from rdflib import Graph

from middleware.linked_data.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType
from middleware.linked_data.dataset import DiscoveryResult, UrlDiscoveryResult
from middleware.linked_data.errors import LinkedDataError

DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 15.0
DEFAULT_MAX_REQUESTS_PER_SECOND = 2.0
EXPECTED_CALLS = 2


class FakeSitemap:
    """A lightweight fake sitemap for unit tests."""

    def __init__(self, urls: list[str]) -> None:
        """Initialize the fake sitemap with a list of URLs."""
        self._urls = urls

    async def discover(self) -> AsyncGenerator[UrlDiscoveryResult, None]:
        """Yield each URL wrapped in a discovery result."""
        for url in self._urls:
            yield UrlDiscoveryResult(url)

    async def get_expected_count(self) -> int | None:
        """Return the expected number of discovery URLs."""
        return len(self._urls)


class BadFakeDataset:
    """A dataset implementation that fails during discovery conversion."""

    def __init__(self, url: str, _client: httpx.AsyncClient | None = None, _config: Config | None = None) -> None:
        """Initialize a dataset that always fails conversion."""
        self._url = url

    @property
    def identifier(self) -> str:
        """Return the dataset identifier."""
        return self._url

    @classmethod
    def from_discovery_result(
        cls,
        _discovery_result: DiscoveryResult,
        client: httpx.AsyncClient | None = None,
        config: Config | None = None,
    ) -> "BadFakeDataset":
        """Raise a fake conversion failure for any discovery result."""
        if client is not None or config is not None:
            del client, config
        raise LinkedDataError("bad dataset")

    async def to_graph(self) -> Graph:
        """Simulate dataset graph conversion (unreachable when from_discovery_result fails)."""
        await asyncio.sleep(0)
        return Graph()


class GoodFakeDataset:
    """A dataset implementation that successfully converts discovery results."""

    def __init__(self, url: str, _client: httpx.AsyncClient | None = None, _config: Config | None = None) -> None:
        """Initialize a fake dataset with a resolved URL."""
        self._url = url

    @property
    def identifier(self) -> str:
        """Return the dataset identifier."""
        return self._url

    @classmethod
    def from_discovery_result(
        cls,
        discovery_result: UrlDiscoveryResult,
        client: httpx.AsyncClient | None = None,
        config: Config | None = None,
    ) -> "GoodFakeDataset":
        """Create a fake dataset from a discovery result."""
        if client is not None or config is not None:
            del client, config
        return cls(discovery_result.url)

    async def to_graph(self) -> Graph:
        """Return an empty rdflib Graph, matching Dataset.to_graph()."""
        await asyncio.sleep(0)
        return Graph()


_MINIMAL_CONFIG = Config(
    sitemap_url="https://example.org/sitemap.xml",
    sitemap_type=SitemapType.xml,
    dataset_type=DatasetType.html_jsonld,
    payload_type=PayloadType.schema_org_general,
    http=NiceHttpClientConfig(),
)

SIMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "My Dataset",
    "identifier": "https://example.org/dataset/1"
  }
  </script>
</head>
<body></body>
</html>"""

MULTI_BLOCK_HTML = """<!DOCTYPE html>
<html>
<head>
  <script type="application/ld+json">
  {"@context": "https://schema.org", "@type": "Dataset", "name": "First"}
  </script>
  <script type="application/ld+json">
  {"@context": "https://schema.org", "@type": "Dataset", "name": "Second"}
  </script>
</head>
<body></body>
</html>"""

NO_JSONLD_HTML = """<!DOCTYPE html><html><head></head><body><p>No JSON-LD here.</p></body></html>"""

BAD_JSON_HTML = """<!DOCTYPE html>
<html><head>
  <script type="application/ld+json">not valid json{{{</script>
</head><body></body></html>"""
