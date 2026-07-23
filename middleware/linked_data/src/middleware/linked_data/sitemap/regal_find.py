"""Regal /find sitemap implementation for Linked Data discovery."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import urlencode, urlparse, urlunparse

from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient

from ..config import Config, SitemapType
from ..dataset import DiscoveryResult, JsonLdDiscoveryResult
from ..errors import LinkedDataSitemapError
from ..json_types import JsonValue
from .sitemap import Sitemap

_REGAL_FIND_QUERY = "contentType:researchData"
_REGAL_FIND_FORMAT = "json"


@Sitemap.register(SitemapType.regal_find)
class RegalFindSitemap(Sitemap):
    """Sitemap parser for Regal `/find` JSON endpoints with inline metadata."""

    def __init__(self, config: Config, client: NiceHttpClient) -> None:
        """Initialize the Regal find sitemap parser."""
        super().__init__(config, client)
        self._page_size = config.page_size

    async def get_expected_count(self) -> int | None:
        """Return None; Regal `/find` does not expose a total hit count."""
        return None

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        offset = 0
        while True:
            page = await self._fetch_page(self.config.sitemap_url, client, offset)
            if not page:
                break

            for index, item in enumerate(page):
                synthetic_id = f"regal_find:from={offset}:index={index}"
                if not isinstance(item, dict):
                    yield RecordProcessingError(
                        (
                            f"Regal /find array element at from={offset} index={index} "
                            f"is not an object (got {type(item).__name__})"
                        ),
                        synthetic_id,
                    )
                    continue

                identifier = self._record_identifier(item)
                if identifier is None:
                    yield RecordProcessingError(
                        (
                            f"Regal /find record at from={offset} index={index} "
                            f"is missing @id (keys={sorted(item.keys())})"
                        ),
                        synthetic_id,
                    )
                    continue

                yield JsonLdDiscoveryResult(identifier=identifier, payload=item)

            if len(page) < self._page_size:
                break
            offset += len(page)

    async def _fetch_page(
        self,
        sitemap_url: str,
        client: NiceHttpClient,
        offset: int,
    ) -> list[JsonValue]:
        request_url = self._build_request_url(sitemap_url, offset, self._page_size)
        response = await client.get_with_policy(request_url)

        payload = response.json()
        if not isinstance(payload, list):
            raise LinkedDataSitemapError(f"Regal /find response must be a JSON array (got {type(payload).__name__})")
        return payload

    @staticmethod
    def _record_identifier(record: dict[str, object]) -> str | None:
        """Return the Regal ``@id``; DOI is not used as a discovery identity."""
        record_id = record.get("@id")
        if isinstance(record_id, str) and record_id.strip():
            return record_id.strip()
        return None

    @staticmethod
    def _build_request_url(sitemap_url: str, offset: int, page_size: int) -> str:
        """Build a `/find` request URL from a query-free base URL.

        Query parameters (`q`, `format`, `from`, `until`) are always set by the
        software. Any query string already present on ``sitemap_url`` is ignored.
        """
        parsed_url = urlparse(sitemap_url)
        query = urlencode(
            [
                ("q", _REGAL_FIND_QUERY),
                ("format", _REGAL_FIND_FORMAT),
                ("from", str(offset)),
                ("until", str(page_size)),
            ]
        )
        return urlunparse(parsed_url._replace(query=query, params="", fragment=""))
