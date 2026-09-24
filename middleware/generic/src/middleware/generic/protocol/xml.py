"""XML sitemap Protocol implementation."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from xml.etree.ElementTree import ParseError

from defusedxml.ElementTree import fromstring  # type: ignore[import-untyped]

from middleware.generic.config import ProtocolType
from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult


@Protocol.register(ProtocolType.xml)
class XmlProtocol(Protocol):
    """Protocol parser for XML sitemap sources."""

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        seen_sitemaps: set[str] = set()
        sitemap_url = self.config.sitemap_url
        async for discovery_result in self._fetch_sitemap(sitemap_url, client, seen_sitemaps):
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

        try:
            root = fromstring(response.text)
        except (ParseError, ValueError, TypeError) as exc:
            raise GenericProtocolError(f"Failed to parse XML sitemap {sitemap_url}: {exc}") from exc

        root_name = self._local_name(root.tag)

        if root_name == "urlset":
            for index, loc in enumerate(root.findall(".//{*}loc")):
                if not loc.text or not loc.text.strip():
                    yield RecordProcessingError(
                        f"XML sitemap {sitemap_url} has empty <loc> at index={index}",
                        f"xml_sitemap:{sitemap_url}:index={index}",
                    )
                    continue

                yield UrlDiscoveryResult(loc.text.strip())
            return

        if root_name == "sitemapindex":
            for index, loc in enumerate(root.findall(".//{*}loc")):
                if not loc.text or not loc.text.strip():
                    yield RecordProcessingError(
                        f"XML sitemap {sitemap_url} has empty <loc> at index={index}",
                        f"xml_sitemap:{sitemap_url}:index={index}",
                    )
                    continue

                nested_sitemap_url = loc.text.strip()
                async for dataset in self._fetch_sitemap(
                    nested_sitemap_url,
                    client,
                    seen_sitemaps,
                ):
                    yield dataset
            return

        raise GenericProtocolError(f"Unsupported sitemap root element: {root_name} (sitemap {sitemap_url})")

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]
