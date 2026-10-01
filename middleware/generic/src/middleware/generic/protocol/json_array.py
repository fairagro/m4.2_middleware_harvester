"""Shared base for Protocols whose response is a JSON array of inline JSON-LD records.

Concrete Protocols differ only in *how the array is fetched* (one static
document vs. offset pagination) and *how a record's discovery identity is
derived* (a required ``@id`` vs. a content-hash composite). Everything else —
JSON array validation, rejecting non-object elements without stopping
discovery, and yielding inline ``JsonLdDiscoveryResult`` units — lives here.

Parsing the record payload is the PayloadParser's job and vocabulary mapping is
the DataMapper's; nothing here is RDI-specific.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncGenerator

from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, JsonLdDiscoveryResult


class JsonArrayProtocol(Protocol):
    """Abstract Protocol for sources that serve JSON arrays of JSON-LD record objects."""

    #: Prefix for synthetic record ids of failures (``<prefix>:<position>``).
    record_id_prefix: str = "json_array"
    #: Human-readable source kind used in failure messages.
    source_label: str = "JSON array"

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        async for position, page in self._pages(client):
            for index, item in enumerate(page):
                parts = (*position, f"index={index}")
                location = " ".join(parts)
                synthetic_id = ":".join((self.record_id_prefix, *parts))
                if not isinstance(item, dict):
                    yield RecordProcessingError(
                        f"{self.source_label} array element at {location} is not an object (got {type(item).__name__})",
                        synthetic_id,
                    )
                    continue

                identifier = self._record_identifier(item)
                if identifier is None:
                    yield RecordProcessingError(
                        f"{self.source_label} record at {location} is missing @id (keys={sorted(item.keys())})",
                        synthetic_id,
                    )
                    continue

                yield self._discovery_result(identifier, item)

    @abstractmethod
    async def _pages(self, client: NiceHttpClient) -> AsyncGenerator[tuple[tuple[str, ...], list[object]], None]:
        """Yield ``(position, array)`` pages.

        ``position`` holds ``key=value`` parts that locate the page in failure
        messages and synthetic record ids (e.g. ``("from=200",)``; empty for a
        single static document).
        """
        if False:  # pragma: no cover  # noqa: make this an async generator
            yield (), []
        raise NotImplementedError

    @abstractmethod
    def _record_identifier(self, record: dict[str, object]) -> str | None:
        """Return the record's discovery identity, or ``None`` when it has none."""

    def _discovery_result(self, identifier: str, record: dict[str, object]) -> JsonLdDiscoveryResult:  # noqa: PLR6301
        """Build the inline discovery unit for one record."""
        return JsonLdDiscoveryResult(identifier=identifier, payload=record)

    async def _fetch_array(self, url: str, client: NiceHttpClient) -> list[object]:
        """GET ``url`` and return its top-level JSON array.

        HTTP/transport errors propagate unchanged (``GenericPlugin`` wraps them);
        an unparseable body or a non-array top level raises ``GenericProtocolError``.
        """
        response = await client.get_with_policy(url)
        try:
            payload = response.json()
        except ValueError as exc:
            raise GenericProtocolError(f"Failed to fetch/parse {self.source_label} {url}: {exc}") from exc
        if not isinstance(payload, list):
            raise GenericProtocolError(
                f"{self.source_label} response must be a JSON array (got {type(payload).__name__})"
            )
        return payload
