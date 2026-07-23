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
        """Build a Solr request URL, overriding ``start``.

        Keep ``rows`` from ``sitemap_url`` when present (``rows`` is a page-size
        parameter). Otherwise set ``rows`` from config ``page_size``.
        """
        parsed_url = urlparse(sitemap_url)
        query_pairs: list[tuple[str, str]] = []
        has_rows = False
        for name, value in parse_qsl(parsed_url.query, keep_blank_values=True):
            if name == "start":
                continue
            if name == "rows":
                has_rows = True
            query_pairs.append((name, value))

        if not has_rows:
            query_pairs.append(("rows", str(page_size)))
        query_pairs.append(("start", str(start)))
        return urlunparse(parsed_url._replace(query=urlencode(query_pairs)))

    @staticmethod
    def _build_base_url(sitemap_url: str) -> str:
        parsed_url = urlparse(sitemap_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid sitemap URL: {sitemap_url}")
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
