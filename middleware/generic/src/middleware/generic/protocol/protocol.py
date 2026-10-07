"""Protocol ABC, registry, type enum, and shared type-config base."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel, ConfigDict

from middleware.contracts.errors import RecordProcessingError, SkippedRecord
from middleware.contracts.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.payload.registry import Registry

type ProtocolYield = DiscoveryResult | RecordProcessingError | SkippedRecord

TProtocol = TypeVar("TProtocol", bound="Protocol")


class ProtocolType(StrEnum):
    """Registered Protocol kinds for generic harvesting."""

    xml = "xml"
    mycore_solr = "mycore_solr"
    dcat_ap = "dcat_ap"
    pubplant_json_array = "pubplant_json_array"
    regal_find = "regal_find"


class ProtocolTypeConfig(BaseModel):
    """Base for type-specific Protocol configs (fields are defined per type)."""

    model_config = ConfigDict(populate_by_name=True)


class Protocol(ABC):
    """Abstract discovery/transport provider for the generic harvest plugin."""

    registry: Registry[ProtocolType, Protocol] = Registry()

    def __init__(self, config: ProtocolTypeConfig, client: NiceHttpClient) -> None:
        """Create a Protocol for type-specific ``config`` and shared ``client``."""
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
