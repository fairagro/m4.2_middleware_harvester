"""MyCoRe Solr sitemap — shim over ``middleware.generic`` MycoreSolrProtocol."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.mycore_solr import MycoreSolrProtocol, MycoreSolrProtocolConfig
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import Config, SitemapType
from middleware.linked_data.errors import LinkedDataSitemapError
from middleware.linked_data.sitemap.sitemap import Sitemap
from middleware.parsing.discovery import DiscoveryResult


@Sitemap.register(SitemapType.mycore_solr)
class MycoreSolrSitemap(Sitemap):
    """Sitemap parser for MyCoRe Solr discovery (delegates to MycoreSolrProtocol)."""

    def __init__(self, config: Config, client: NiceHttpClient) -> None:
        """Initialize the shim and a shared Protocol instance (preserves page cache)."""
        super().__init__(config, client)
        protocol_config = MycoreSolrProtocolConfig(entry_url=config.sitemap_url, page_size=config.page_size)
        self._protocol = MycoreSolrProtocol(protocol_config, client)

    async def get_expected_count(self) -> int | None:
        """Return the total number of matching results via the Protocol."""
        try:
            return await self._protocol.get_expected_count()
        except GenericProtocolError as exc:
            raise LinkedDataSitemapError(str(exc)) from exc

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        try:
            async for discovery_result in self._protocol._discover(client):  # noqa: SLF001
                yield discovery_result
        except GenericProtocolError as exc:
            raise LinkedDataSitemapError(str(exc)) from exc
