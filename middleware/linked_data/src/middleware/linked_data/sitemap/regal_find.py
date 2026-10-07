"""Regal /find sitemap implementation — shim over ``middleware.generic`` RegalFindProtocol."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from middleware.contracts.errors import RecordProcessingError
from middleware.contracts.nice_http_client import NiceHttpClient
from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.regal_find import RegalFindProtocol, RegalFindProtocolConfig
from middleware.linked_data.config import Config, SitemapType
from middleware.linked_data.errors import LinkedDataSitemapError
from middleware.linked_data.sitemap.sitemap import Sitemap
from middleware.parsing.discovery import DiscoveryResult


@Sitemap.register(SitemapType.regal_find)
class RegalFindSitemap(Sitemap):
    """Sitemap parser for Regal `/find` JSON endpoints (delegates to RegalFindProtocol)."""

    def __init__(self, config: Config, client: NiceHttpClient) -> None:
        """Initialize the shim and a shared Protocol instance."""
        super().__init__(config, client)
        protocol_config = RegalFindProtocolConfig(entry_url=config.sitemap_url, page_size=config.page_size)
        self._protocol = RegalFindProtocol(protocol_config, client)

    async def get_expected_count(self) -> int | None:
        """Return None; Regal `/find` does not expose a total hit count."""
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
