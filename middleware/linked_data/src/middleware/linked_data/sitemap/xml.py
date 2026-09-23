"""XML sitemap implementation — shim over ``middleware.generic`` XmlProtocol."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from middleware.generic.discovery import DiscoveryResult
from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.xml import XmlProtocol
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import SitemapType
from middleware.linked_data.errors import LinkedDataSitemapError
from middleware.linked_data.sitemap.sitemap import Sitemap


@Sitemap.register(SitemapType.xml)
class XmlSitemap(Sitemap):
    """Sitemap parser for XML sitemap protocol sources (delegates to XmlProtocol)."""

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        protocol = XmlProtocol(self.config, client)
        try:
            async for discovery_result in protocol._discover(client):  # noqa: SLF001
                yield discovery_result
        except GenericProtocolError as exc:
            raise LinkedDataSitemapError(str(exc)) from exc
