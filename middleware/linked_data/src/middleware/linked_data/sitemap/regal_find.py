"""Regal /find sitemap implementation for Linked Data discovery."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient

from ..config import Config, SitemapType
from ..dataset import DiscoveryResult, JsonLdDiscoveryResult
from ..errors import LinkedDataSitemapError
from ..json_types import JsonValue
from .sitemap import Sitemap

# Overridable defaults when absent from ``sitemap_url``. Operator-supplied
# query parameters always win for these (and any other non-owned keys).
_DEFAULT_REGAL_PARAMS: tuple[tuple[str, str], ...] = (("q", "contentType:researchData"),)

# Owned by the harvester: never taken from ``sitemap_url``.
# ``until`` is resolved once (URL override or config ``page_size``) and always
# written by the software so pagination stop conditions stay consistent.
_SOFTWARE_REGAL_PARAMS: tuple[tuple[str, str], ...] = (("format", "json"),)
_SOFTWARE_OWNED_QUERY_NAMES = frozenset({"from", "format", "until"})


@Sitemap.register(SitemapType.regal_find)
class RegalFindSitemap(Sitemap):
    """Sitemap parser for Regal `/find` JSON endpoints with inline metadata."""

    def __init__(self, config: Config, client: NiceHttpClient) -> None:
        """Initialize the Regal find sitemap parser."""
        super().__init__(config, client)
        self._page_size = self._resolve_page_size(config.sitemap_url, config.page_size)

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
    def _resolve_page_size(sitemap_url: str, page_size: int) -> int:
        """Return URL ``until`` when present and valid; otherwise config ``page_size``."""
        for name, value in parse_qsl(urlparse(sitemap_url).query, keep_blank_values=True):
            if name != "until":
                continue
            try:
                parsed = int(value)
            except ValueError:
                break
            if parsed >= 1:
                return parsed
            break
        return page_size

    @staticmethod
    def _build_request_url(sitemap_url: str, offset: int, page_size: int) -> str:
        """Build a `/find` request URL with defaults and operator overrides.

        ``sitemap_url`` may be a query-free `/find` endpoint. Missing
        overridable parameters (notably ``q``) are filled from defaults.
        Operator-supplied values for those keys win; extra filter/sort params
        are forwarded. ``format=json``, pagination ``from``, and ``until``
        (resolved from URL ``until`` or config ``page_size``) are always set
        by the software because discovery parses a JSON array response.
        """
        parsed_url = urlparse(sitemap_url)
        operator_pairs = [
            (name, value)
            for name, value in parse_qsl(parsed_url.query, keep_blank_values=True)
            if name not in _SOFTWARE_OWNED_QUERY_NAMES
        ]
        operator_names = {name for name, _ in operator_pairs}

        query_pairs: list[tuple[str, str]] = [
            (name, value) for name, value in _DEFAULT_REGAL_PARAMS if name not in operator_names
        ]
        query_pairs.extend(operator_pairs)
        query_pairs.extend(_SOFTWARE_REGAL_PARAMS)
        query_pairs.append(("until", str(page_size)))
        query_pairs.append(("from", str(offset)))
        return urlunparse(parsed_url._replace(query=urlencode(query_pairs), params="", fragment=""))
