"""Schema.org sitemap implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from typing import TypeVar

import httpx
from defusedxml.ElementTree import fromstring  # type: ignore[import]

from .config import Config, SitemapType
from .dataset import DiscoveryResult, UrlDiscoveryResult

S = TypeVar("S", bound="Sitemap")


class Sitemap(ABC):
    """Abstract sitemap provider that yields discovery results asynchronously."""

    registry: dict[SitemapType, type[Sitemap]] = {}

    def __init__(self, config: Config, client: httpx.AsyncClient) -> None:
        """Create a new Sitemap configured for a specific source."""
        self.config = config
        self._client = client

    async def discover(self) -> AsyncGenerator[DiscoveryResult, None]:
        """Asynchronously yield raw discovery results using the provided HTTP client."""
        async for result in self._discover(self._client):
            yield result

    @abstractmethod
    async def _discover(self, client: httpx.AsyncClient) -> AsyncGenerator[DiscoveryResult, None]:
        """Discover dataset sources using the provided HTTP client."""
        if False:  # pragma: no cover
            yield UrlDiscoveryResult("")
        raise NotImplementedError

    @classmethod
    def register(cls, sitemap_type: SitemapType) -> Callable[[type[S]], type[S]]:
        """Register a concrete Sitemap implementation for the given sitemap type."""

        def decorator(subclass: type[S]) -> type[S]:
            cls.registry[sitemap_type] = subclass
            return subclass

        return decorator


@Sitemap.register(SitemapType.xml)
class XmlSitemap(Sitemap):
    """Sitemap parser for XML sitemap protocol sources."""

    async def _discover(self, client: httpx.AsyncClient) -> AsyncGenerator[DiscoveryResult, None]:
        seen_sitemaps: set[str] = set()
        seen_dataset_urls: set[str] = set()

        async for discovery_result in self._fetch_sitemap(
            self.config.sitemap_url,
            client,
            seen_sitemaps,
            seen_dataset_urls,
        ):
            yield discovery_result

    async def _fetch_sitemap(
        self,
        sitemap_url: str,
        client: httpx.AsyncClient,
        seen_sitemaps: set[str],
        seen_dataset_urls: set[str],
    ) -> AsyncGenerator[DiscoveryResult, None]:
        if sitemap_url in seen_sitemaps:
            return

        seen_sitemaps.add(sitemap_url)
        response = await client.get(sitemap_url)
        response.raise_for_status()

        root = fromstring(response.text)
        root_name = self._local_name(root.tag)

        if root_name == "urlset":
            for loc in root.findall(".//{*}loc"):
                if not loc.text:
                    continue

                dataset_url = loc.text.strip()
                if dataset_url in seen_dataset_urls:
                    continue

                seen_dataset_urls.add(dataset_url)
                yield UrlDiscoveryResult(dataset_url)

            return

        if root_name == "sitemapindex":
            for loc in root.findall(".//{*}loc"):
                if loc.text:
                    nested_sitemap_url = loc.text.strip()
                    async for dataset in self._fetch_sitemap(
                        nested_sitemap_url,
                        client,
                        seen_sitemaps,
                        seen_dataset_urls,
                    ):
                        yield dataset
            return

        raise ValueError(f"Unsupported sitemap root element: {root_name}")

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]
