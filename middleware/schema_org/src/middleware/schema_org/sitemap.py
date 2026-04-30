"""Schema.org sitemap implementations."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable

import httpx
from defusedxml.ElementTree import fromstring  # type: ignore[import]

from .config import Config, SitemapType
from .interfaces import Dataset, DummyDataset, Sitemap


@Sitemap.register(SitemapType.xml)
class XmlSitemap(Sitemap):
    """Sitemap parser for XML sitemap protocol sources."""

    def __init__(
        self,
        config: Config,
        dataset_factory: Callable[[str], Dataset] = DummyDataset,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize an XML sitemap parser with optional dataset construction."""
        super().__init__(config)
        self._dataset_factory = dataset_factory
        self._client = client

    async def discover(self) -> AsyncGenerator[Dataset, None]:
        """Asynchronously yield Dataset objects from configured XML sitemap URLs."""
        seen_sitemaps: set[str] = set()
        yielded_datasets: set[str] = set()

        if self._client is not None:
            async for dataset in self._discover_with_client(self._client, seen_sitemaps, yielded_datasets):
                yield dataset
            return

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async for dataset in self._discover_with_client(client, seen_sitemaps, yielded_datasets):
                yield dataset

    async def _discover_with_client(
        self,
        client: httpx.AsyncClient,
        seen_sitemaps: set[str],
        yielded_datasets: set[str],
    ) -> AsyncGenerator[Dataset, None]:
        for sitemap_url in self.config.sitemap_urls:
            async for dataset in self._fetch_sitemap(sitemap_url, client, seen_sitemaps, yielded_datasets):
                yield dataset

    async def _fetch_sitemap(
        self,
        sitemap_url: str,
        client: httpx.AsyncClient,
        seen_sitemaps: set[str],
        yielded_datasets: set[str],
    ) -> AsyncGenerator[Dataset, None]:
        if sitemap_url in seen_sitemaps:
            return

        seen_sitemaps.add(sitemap_url)
        response = await client.get(sitemap_url)
        response.raise_for_status()

        root = fromstring(response.text)
        root_name = self._local_name(root.tag)

        if root_name == "urlset":
            for loc in root.findall(".//{*}loc"):
                if not loc.text:
                    continue

                dataset_url = loc.text.strip()
                if dataset_url in yielded_datasets:
                    continue

                yielded_datasets.add(dataset_url)
                yield self._dataset_factory(dataset_url)

            return

        if root_name == "sitemapindex":
            for loc in root.findall(".//{*}loc"):
                if loc.text:
                    async for dataset in self._fetch_sitemap(loc.text.strip(), client, seen_sitemaps, yielded_datasets):
                        yield dataset
            return

        raise ValueError(f"Unsupported sitemap root element: {root_name}")

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]
