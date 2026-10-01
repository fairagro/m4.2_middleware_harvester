"""Regal /find sitemap implementation — shim over ``middleware.generic`` RegalFindProtocol."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.regal_find import RegalFindProtocol
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import SitemapType
from middleware.linked_data.errors import LinkedDataSitemapError
from middleware.linked_data.sitemap.sitemap import Sitemap
from middleware.parsing.discovery import DiscoveryResult


@Sitemap.register(SitemapType.regal_find)
class RegalFindSitemap(Sitemap):
    """Sitemap parser for Regal `/find` JSON endpoints (delegates to RegalFindProtocol)."""

    async def get_expected_count(self) -> int | None:  # noqa: PLR6301
        """Return None; Regal `/find` does not expose a total hit count."""
        return None

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        protocol = RegalFindProtocol(self.config, client)
        try:
            async for discovery_result in protocol._discover(client):  # noqa: SLF001
                yield discovery_result
        except GenericProtocolError as exc:
            raise LinkedDataSitemapError(str(exc)) from exc
