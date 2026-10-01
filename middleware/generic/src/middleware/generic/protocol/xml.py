"""XML sitemap Protocol implementation."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated
from xml.etree.ElementTree import ParseError

from defusedxml.ElementTree import fromstring  # type: ignore[import-untyped]
from pydantic import ConfigDict, Field

from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.protocol import Protocol, ProtocolType, ProtocolTypeConfig
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult


class XmlProtocolConfig(ProtocolTypeConfig):
    """Type-specific config for the XML sitemap Protocol."""

    model_config = ConfigDict(populate_by_name=True)

    entry_url: Annotated[
        str,
        Field(description="XML sitemap entry-point URL (urlset or sitemapindex)."),
    ]


@Protocol.register(ProtocolType.xml)
class XmlProtocol(Protocol):
    """Protocol parser for XML sitemap sources."""

    config: XmlProtocolConfig

    def __init__(self, config: XmlProtocolConfig, client: NiceHttpClient) -> None:
        """Create an XML sitemap Protocol."""
        super().__init__(config, client)

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        seen_sitemaps: set[str] = set()
        entry_url = self.config.entry_url
        async for discovery_result in self._fetch_sitemap(entry_url, client, seen_sitemaps):
            yield discovery_result

    async def _fetch_sitemap(
        self,
        entry_url: str,
        client: NiceHttpClient,
        seen_sitemaps: set[str],
    ) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        if entry_url in seen_sitemaps:
            return

        seen_sitemaps.add(entry_url)
        response = await client.get_with_policy(entry_url)

        try:
            root = fromstring(response.text)
        except (ParseError, ValueError, TypeError) as exc:
            raise GenericProtocolError(f"Failed to parse XML sitemap {entry_url}: {exc}") from exc

        root_name = self._local_name(root.tag)

        if root_name == "urlset":
            for index, loc in enumerate(root.findall(".//{*}loc")):
                if not loc.text or not loc.text.strip():
                    yield RecordProcessingError(
                        f"XML sitemap {entry_url} has empty <loc> at index={index}",
                        f"xml_sitemap:{entry_url}:index={index}",
                    )
                    continue

                yield UrlDiscoveryResult(loc.text.strip())
            return

        if root_name == "sitemapindex":
            for index, loc in enumerate(root.findall(".//{*}loc")):
                if not loc.text or not loc.text.strip():
                    yield RecordProcessingError(
                        f"XML sitemap {entry_url} has empty <loc> at index={index}",
                        f"xml_sitemap:{entry_url}:index={index}",
                    )
                    continue

                nested_entry_url = loc.text.strip()
                async for dataset in self._fetch_sitemap(
                    nested_entry_url,
                    client,
                    seen_sitemaps,
                ):
                    yield dataset
            return

        raise GenericProtocolError(f"Unsupported sitemap root element: {root_name} (sitemap {entry_url})")

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]
