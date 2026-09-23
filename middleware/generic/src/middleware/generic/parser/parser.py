"""PayloadParser ABC and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import ClassVar, TypeVar

from middleware.generic.config import ParserType
from middleware.generic.discovery import DiscoveryResult
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload
from middleware.payload.registry import Registry

TParser = TypeVar("TParser", bound="PayloadParser")


class PayloadParser(ABC):
    """Turns a discovery unit into a typed ``ParsedPayload``."""

    registry: Registry[ParserType, PayloadParser] = Registry()
    produces: ClassVar[PayloadKind]

    @classmethod
    def register(cls, parser_type: ParserType) -> Callable[[type[TParser]], type[TParser]]:
        """Register a concrete PayloadParser for the given type."""
        return cls.registry.register(parser_type)

    @abstractmethod
    async def parse(
        self,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: object,
    ) -> ParsedPayload:
        """Parse ``discovery_result`` into a ``ParsedPayload``."""
        raise NotImplementedError
