"""Schema.org sitemap implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from typing import TypeVar, cast

import httpx

from ..config import Config, SitemapType
from ..dataset import DiscoveryResult, DuplicateUrlDiscoveryResult, UrlDiscoveryResult
from ..registry import Registry

S = TypeVar("S", bound="Sitemap")


class Sitemap(ABC):
    """Abstract sitemap provider that yields discovery results asynchronously."""

    registry: Registry[SitemapType, Sitemap] = Registry()

    def __init__(self, config: Config, client: httpx.AsyncClient) -> None:
        """Create a new Sitemap configured for a specific source."""
        self.config = config
        self._client = client

    async def discover(self) -> AsyncGenerator[DiscoveryResult, None]:
        """Asynchronously yield raw discovery results using the provided HTTP client.

        Deduplicates results by URL — each URL is yielded at most once.
        """
        seen: set[str] = set()
        async for result in self._discover(self._client):
            if isinstance(result, UrlDiscoveryResult):
                if result.url in seen:
                    yield DuplicateUrlDiscoveryResult(result.url)
                    continue
                seen.add(result.url)
            yield result

    async def get_expected_count(self) -> int | None:
        """Return the expected number of discovery results, if known."""
        return None

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
            cls.registry[sitemap_type] = cast(type[Sitemap], subclass)
            return subclass

        return decorator
