"""XML sitemap implementation for Linked Data dataset discovery."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from defusedxml.ElementTree import fromstring  # type: ignore[import]

from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient

from ..config import SitemapType
from ..dataset import DiscoveryResult, UrlDiscoveryResult
from .sitemap import Sitemap


@Sitemap.register(SitemapType.xml)
class XmlSitemap(Sitemap):
    """Sitemap parser for XML sitemap protocol sources."""

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        seen_sitemaps: set[str] = set()

        async for discovery_result in self._fetch_sitemap(
            self.config.sitemap_url,
            client,
            seen_sitemaps,
        ):
            yield discovery_result

    async def _fetch_sitemap(
        self,
        sitemap_url: str,
        client: NiceHttpClient,
        seen_sitemaps: set[str],
    ) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        if sitemap_url in seen_sitemaps:
            return

        seen_sitemaps.add(sitemap_url)
        response = await client.get_with_policy(sitemap_url)

        root = fromstring(response.text)
        root_name = self._local_name(root.tag)

        if root_name == "urlset":
            for index, loc in enumerate(root.findall(".//{*}loc")):
                if not loc.text or not loc.text.strip():
                    yield RecordProcessingError(
                        f"XML sitemap {sitemap_url} has empty <loc> at index={index}",
                        f"xml_sitemap:index={index}",
                    )
                    continue

                yield UrlDiscoveryResult(loc.text.strip())
            return

        if root_name == "sitemapindex":
            for loc in root.findall(".//{*}loc"):
                if loc.text:
                    nested_sitemap_url = loc.text.strip()
                    async for dataset in self._fetch_sitemap(
                        nested_sitemap_url,
                        client,
                        seen_sitemaps,
                    ):
                        yield dataset
            return

        raise ValueError(f"Unsupported sitemap root element: {root_name}")

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]
