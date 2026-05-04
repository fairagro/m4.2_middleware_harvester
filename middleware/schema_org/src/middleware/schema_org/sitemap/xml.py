"""XML sitemap implementation for Schema.org dataset discovery."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx
from defusedxml.ElementTree import fromstring  # type: ignore[import]

from ..config import SitemapType
from ..dataset import DiscoveryResult, UrlDiscoveryResult
from .sitemap import Sitemap


@Sitemap.register(SitemapType.xml)
class XmlSitemap(Sitemap):
    """Sitemap parser for XML sitemap protocol sources."""

    async def _discover(self, client: httpx.AsyncClient) -> AsyncGenerator[DiscoveryResult, None]:
        seen_sitemaps: set[str] = set()
        seen_dataset_urls: set[str] = set()

        async for discovery_result in self._fetch_sitemap(
            self.config.sitemap_url,
            client,
            seen_sitemaps,
            seen_dataset_urls,
        ):
            yield discovery_result

    async def _fetch_sitemap(
        self,
        sitemap_url: str,
        client: httpx.AsyncClient,
        seen_sitemaps: set[str],
        seen_dataset_urls: set[str],
    ) -> AsyncGenerator[DiscoveryResult, None]:
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
                if dataset_url in seen_dataset_urls:
                    continue

                seen_dataset_urls.add(dataset_url)
                yield UrlDiscoveryResult(dataset_url)

            return

        if root_name == "sitemapindex":
            for loc in root.findall(".//{*}loc"):
                if loc.text:
                    nested_sitemap_url = loc.text.strip()
                    async for dataset in self._fetch_sitemap(
                        nested_sitemap_url,
                        client,
                        seen_sitemaps,
                        seen_dataset_urls,
                    ):
                        yield dataset
            return

        raise ValueError(f"Unsupported sitemap root element: {root_name}")

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]
