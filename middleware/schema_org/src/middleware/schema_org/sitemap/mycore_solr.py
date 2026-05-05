"""MyCoRe Solr sitemap implementation for Schema.org dataset discovery."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

from ..config import SitemapType
from ..dataset import DiscoveryResult, UrlDiscoveryResult
from .sitemap import Sitemap


@Sitemap.register(SitemapType.mycore_solr)
class MycoreSolrSitemap(Sitemap):
    """Sitemap parser for MyCoRe Solr-based discovery endpoints."""

    async def _discover(self, client: httpx.AsyncClient) -> AsyncGenerator[DiscoveryResult, None]:
        base_url = self._build_base_url(self.config.sitemap_url)
        start = 0
        seen_dataset_urls: set[str] = set()

        while True:
            num_found, docs, returned_start = await self._fetch_page(self.config.sitemap_url, client, start)
            if not docs:
                break

            for doc in docs:
                if not isinstance(doc, dict):
                    continue

                object_id = doc.get("id")
                if not isinstance(object_id, str) or not object_id.strip():
                    continue

                dataset_url = f"{base_url}/receive/{object_id}"
                if dataset_url in seen_dataset_urls:
                    continue

                seen_dataset_urls.add(dataset_url)
                yield UrlDiscoveryResult(dataset_url)

            start += len(docs)
            if start >= num_found:
                break

    async def _fetch_page(
        self,
        sitemap_url: str,
        client: httpx.AsyncClient,
        start: int,
    ) -> tuple[int, list[dict[str, object]], int]:
        request_url = self._build_request_url(sitemap_url, start)
        response = await client.get(request_url)
        response.raise_for_status()

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
    def _build_request_url(sitemap_url: str, start: int) -> str:
        parsed_url = urlparse(sitemap_url)
        query_pairs = []
        for name, value in parse_qsl(parsed_url.query, keep_blank_values=True):
            if name == "start":
                continue
            query_pairs.append((name, value))

        query_pairs.append(("start", str(start)))
        query = urlencode(query_pairs)
        return urlunparse(parsed_url._replace(query=query))

    @staticmethod
    def _build_base_url(sitemap_url: str) -> str:
        parsed_url = urlparse(sitemap_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid sitemap URL: {sitemap_url}")
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
