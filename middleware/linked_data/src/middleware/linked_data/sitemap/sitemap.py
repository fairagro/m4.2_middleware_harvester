"""Linked Data sitemap implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from typing import TypeVar, cast

from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import NiceHttpClient

from ..config import Config, SitemapType
from ..dataset import DiscoveryResult, UrlDiscoveryResult
from ..registry import Registry

S = TypeVar("S", bound="Sitemap")

# Payload carriers plus shared harvester signals (inspire-style).
type SitemapYield = DiscoveryResult | RecordProcessingError | SkippedRecord


class Sitemap(ABC):
    """Abstract sitemap provider that yields discovery results asynchronously."""

    registry: Registry[SitemapType, Sitemap] = Registry()

    def __init__(self, config: Config, client: NiceHttpClient) -> None:
        """Create a new Sitemap configured for a specific source."""
        self.config = config
        self._client = client

    async def discover(self) -> AsyncGenerator[SitemapYield, None]:
        """Yield discovery payloads, record failures, or deliberate skips.

        Deduplicates successful ``DiscoveryResult`` entries by ``identifier``.
        ``RecordProcessingError`` from ``_discover`` is forwarded unchanged
        (same contract as the inspire CSW client). Duplicates become
        ``SkippedRecord``.
        """
        seen: set[str] = set()
        async for result in self._discover(self._client):
            if isinstance(result, RecordProcessingError):
                yield result
                continue
            if result.identifier in seen:
                url = result.identifier if isinstance(result, UrlDiscoveryResult) else None
                yield SkippedRecord(
                    f"Duplicate discovery entry skipped: {result.identifier}",
                    url,
                )
                continue
            seen.add(result.identifier)
            yield result

    async def get_expected_count(self) -> int | None:
        """Return the expected number of discovery results, if known."""
        return None

    @abstractmethod
    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        """Discover dataset sources using the shared polite HTTP client."""
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
