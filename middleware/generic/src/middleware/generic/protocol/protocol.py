"""Protocol ABC and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from typing import Protocol as TypingProtocol, TypeVar

from middleware.generic.config import ProtocolType
from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.payload.registry import Registry

type ProtocolYield = DiscoveryResult | RecordProcessingError | SkippedRecord

TProtocol = TypeVar("TProtocol", bound="Protocol")


class SupportsSitemapUrl(TypingProtocol):
    """Minimal config surface required by Protocol implementations."""

    sitemap_url: str


class Protocol(ABC):
    """Abstract discovery/transport provider for the generic harvest plugin."""

    registry: Registry[ProtocolType, Protocol] = Registry()

    def __init__(self, config: SupportsSitemapUrl, client: NiceHttpClient) -> None:
        """Create a Protocol for ``config`` (must expose ``sitemap_url``) and ``client``."""
        self.config = config
        self._client = client

    async def discover(self) -> AsyncGenerator[ProtocolYield, None]:
        """Yield discovery payloads, record failures, or deliberate skips.

        Deduplicates successful ``DiscoveryResult`` entries by ``identifier``.
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

    async def get_expected_count(self) -> int | None:  # noqa: PLR6301
        """Return the expected number of discovery results, if known."""
        return None

    @abstractmethod
    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        """Discover harvest units using the shared polite HTTP client."""
        if False:  # pragma: no cover  # noqa: make this an async generator
            yield UrlDiscoveryResult("")
        raise NotImplementedError

    @classmethod
    def register(cls, protocol_type: ProtocolType) -> Callable[[type[TProtocol]], type[TProtocol]]:
        """Register a concrete Protocol implementation for the given type."""
        return cls.registry.register(protocol_type)
