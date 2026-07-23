"""MyCoRe Solr sitemap implementation for Linked Data dataset discovery."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient

from ..config import Config, SitemapType
from ..dataset import DiscoveryResult, UrlDiscoveryResult
from ..json_types import JsonValue
from .sitemap import Sitemap

# Overridable defaults when absent from ``sitemap_url``. Operator-supplied
# query parameters always win for these. ``q=*:*`` matches Solr's usual
# match-all; narrow with an explicit ``q`` / ``fq`` on the URL when needed.
_DEFAULT_SOLR_PARAMS: tuple[tuple[str, str], ...] = (
    ("core", "main"),
    ("q", "*:*"),
    ("fl", "id"),
)

# Owned by the harvester: never taken from ``sitemap_url``.
_SOFTWARE_SOLR_PARAMS: tuple[tuple[str, str], ...] = (("wt", "json"),)
_SOFTWARE_OWNED_QUERY_NAMES = frozenset({"start", "wt"})


@Sitemap.register(SitemapType.mycore_solr)
class MycoreSolrSitemap(Sitemap):
    """Sitemap parser for MyCoRe Solr-based discovery endpoints."""

    def __init__(self, config: Config, client: NiceHttpClient) -> None:
        """Initialize the MyCoRe Solr sitemap parser and its page cache."""
        super().__init__(config, client)
        self._page_size = config.page_size
        self._first_page_cache: tuple[int, list[JsonValue], int] | None = None

    async def get_expected_count(self) -> int | None:
        """Return the total number of matching results, if the backend exposes it."""
        if self._first_page_cache is not None:
            return self._first_page_cache[0]

        num_found, docs, returned_start = await self._fetch_page(self.config.sitemap_url, self._client, 0)
        self._first_page_cache = (num_found, docs, returned_start)
        return num_found

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        base_url = self._build_base_url(self.config.sitemap_url)
        start = 0

        while True:
            if self._first_page_cache is not None and start == 0:
                num_found, docs, returned_start = self._first_page_cache
                self._first_page_cache = None
            else:
                num_found, docs, returned_start = await self._fetch_page(self.config.sitemap_url, client, start)
            if not docs:
                break

            for index, doc in enumerate(docs):
                synthetic_id = f"mycore_solr:start={start}:index={index}"
                if not isinstance(doc, dict):
                    yield RecordProcessingError(
                        (f"MyCoRe Solr doc at start={start} index={index} is not an object (got {type(doc).__name__})"),
                        synthetic_id,
                    )
                    continue

                object_id = doc.get("id")
                if not isinstance(object_id, str) or not object_id.strip():
                    yield RecordProcessingError(
                        f"MyCoRe Solr doc at start={start} index={index} is missing id",
                        synthetic_id,
                    )
                    continue

                yield UrlDiscoveryResult(f"{base_url}/receive/{object_id.strip()}")

            start += len(docs)
            if start >= num_found:
                break

    async def _fetch_page(
        self,
        sitemap_url: str,
        client: NiceHttpClient,
        start: int,
    ) -> tuple[int, list[JsonValue], int]:
        request_url = self._build_request_url(sitemap_url, start, self._page_size)
        response = await client.get_with_policy(request_url)

        payload = response.json()
        response_object = payload.get("response")
        if not isinstance(response_object, dict):
            raise ValueError("Missing Solr response envelope: response")

        num_found = response_object.get("numFound")
        if not isinstance(num_found, int):
            raise ValueError("Missing or invalid response.numFound")

        returned_start = response_object.get("start")
        if not isinstance(returned_start, int):
            raise ValueError("Missing or invalid response.start")

        docs = response_object.get("docs")
        if not isinstance(docs, list):
            raise ValueError("Missing expected response.docs array")

        return num_found, docs, returned_start

    @staticmethod
    def _build_request_url(sitemap_url: str, start: int, page_size: int) -> str:
        """Build a Solr request URL with defaults and operator overrides.

        ``sitemap_url`` may be a query-free select endpoint
        (e.g. ``https://host/servlets/solr/select``). Missing overridable
        parameters (``core``, ``q``, ``fl``, ``rows``) are filled
        automatically; operator-supplied values for those keys win.
        ``wt=json`` and pagination ``start`` are always set by the software
        (values from ``sitemap_url`` are ignored) because the parser requires
        the Solr JSON response envelope.
        """
        parsed_url = urlparse(sitemap_url)
        operator_pairs = [
            (name, value)
            for name, value in parse_qsl(parsed_url.query, keep_blank_values=True)
            if name not in _SOFTWARE_OWNED_QUERY_NAMES
        ]
        operator_names = {name for name, _ in operator_pairs}

        query_pairs: list[tuple[str, str]] = [
            (name, value) for name, value in _DEFAULT_SOLR_PARAMS if name not in operator_names
        ]
        if "rows" not in operator_names:
            query_pairs.append(("rows", str(page_size)))
        query_pairs.extend(operator_pairs)
        query_pairs.extend(_SOFTWARE_SOLR_PARAMS)
        query_pairs.append(("start", str(start)))
        return urlunparse(parsed_url._replace(query=urlencode(query_pairs), params="", fragment=""))

    @staticmethod
    def _build_base_url(sitemap_url: str) -> str:
        parsed_url = urlparse(sitemap_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid sitemap URL: {sitemap_url}")
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
