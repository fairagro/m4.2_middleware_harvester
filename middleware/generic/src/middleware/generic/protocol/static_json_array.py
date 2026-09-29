"""Static JSON array Protocol implementation (one GET, no pagination).

Fetches a single JSON document whose top level is an array of inline JSON-LD
records (e.g. the PlabiPD/PubPlant ``genomes.json`` Schema.org dump) and yields
one inline ``JsonLdDiscoveryResult`` per array element.

This Protocol only splits the array into records; parsing the record payload
is the ``jsonld`` PayloadParser's job and vocabulary mapping is the DataMapper's.
Nothing here is RDI-specific: the array URL is ``config.sitemap_url``.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncGenerator

from middleware.generic.config import ProtocolType
from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, JsonLdDiscoveryResult
from middleware.payload.linked_data_mapper import LinkedDataMapper


@Protocol.register(ProtocolType.static_json_array)
class StaticJsonArrayProtocol(Protocol):
    """Protocol for a single, non-paginated JSON array of JSON-LD records."""

    async def get_expected_count(self) -> int | None:
        """Return the exact record count; the whole array is fetched in one shot."""
        array = await self._fetch_array(self._client)
        return len(array)

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        array = await self._fetch_array(client)
        for index, item in enumerate(array):
            if not isinstance(item, dict):
                yield RecordProcessingError(
                    f"Static JSON array element at index={index} is not an object (got {type(item).__name__})",
                    f"static_json_array:index={index}",
                )
                continue

            identifier = self._composite_identifier(item)
            yield JsonLdDiscoveryResult(identifier=identifier, payload=item, harvest_source_id=identifier)

    async def _fetch_array(self, client: NiceHttpClient) -> list[object]:
        url = self.config.sitemap_url
        try:
            response = await client.get_with_policy(url)
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            raise GenericProtocolError(f"Failed to fetch/parse static JSON array {url}: {exc}") from exc
        if not isinstance(payload, list):
            raise GenericProtocolError(
                f"Static JSON array response must be a JSON array (got {type(payload).__name__})"
            )
        return payload

    @staticmethod
    def _composite_identifier(record: dict[str, object]) -> str:
        """Build a stable, collision-safe identifier for a JSON-LD record.

        Static JSON array sources may deliberately have several records share
        the same ``@id``/``identifier`` value (e.g. one publication DOI
        describing several distinct genome records). Deriving identity from
        record content rather than array position keeps identifiers stable
        across a source that is rebuilt and re-ordered on every refresh, while
        still giving genuinely distinct records distinct identifiers: content
        differs -> hash differs -> no false dedup; content is byte-identical
        -> hash matches -> correctly collapsed by ``Protocol.discover()``.
        """
        raw_id = record.get("@id") or record.get("identifier") or ""
        doi_part = LinkedDataMapper.sanitize_identifier(str(raw_id))
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        return f"{doi_part}:{digest}" if doi_part else digest
