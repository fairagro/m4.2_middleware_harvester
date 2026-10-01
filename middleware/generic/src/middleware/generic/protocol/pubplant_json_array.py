"""PubPlant JSON array Protocol implementation (one GET, no pagination).

Fetches the PlabiPD/PubPlant ``genomes.json`` Schema.org dump (produced by
``usadellab/pubplant2schemaorg``), a single JSON document whose top level is an
array of inline JSON-LD records, and yields one inline ``JsonLdDiscoveryResult``
per array element.

Array handling is shared with other JSON array sources (``JsonArrayProtocol``);
this Protocol only adds the single-GET page source and a content-hash identity,
because PubPlant records share publication DOIs and carry no unique ``@id``.
The array URL is ``config.entry_url``.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncGenerator
from typing import Annotated

from pydantic import ConfigDict, Field

from middleware.generic.protocol.json_array import JsonArrayProtocol
from middleware.generic.protocol.protocol import Protocol, ProtocolType, ProtocolTypeConfig
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import JsonLdDiscoveryResult
from middleware.payload.linked_data_mapper import LinkedDataMapper


class PubPlantJsonArrayProtocolConfig(ProtocolTypeConfig):
    """Type-specific config for the PubPlant JSON array Protocol."""

    model_config = ConfigDict(populate_by_name=True)

    entry_url: Annotated[
        str,
        Field(description="URL of the PubPlant JSON array document (single GET, no pagination)."),
    ]


@Protocol.register(ProtocolType.pubplant_json_array)
class PubPlantJsonArrayProtocol(JsonArrayProtocol):
    """Protocol for the PubPlant single, non-paginated JSON array of JSON-LD records."""

    config: PubPlantJsonArrayProtocolConfig
    record_id_prefix = "pubplant_json_array"
    source_label = "PubPlant JSON array"

    def __init__(self, config: PubPlantJsonArrayProtocolConfig, client: NiceHttpClient) -> None:
        """Create a PubPlant JSON array Protocol."""
        super().__init__(config, client)

    async def get_expected_count(self) -> int | None:  # noqa: PLR6301
        """Return None; counting would download the whole array a second time.

        ``GenericPlugin.get_expected_datasets()`` and ``run()`` use separate
        Protocol instances, so there is no single fetch to reuse.
        """
        return None

    async def _pages(self, client: NiceHttpClient) -> AsyncGenerator[tuple[tuple[str, ...], list[object]], None]:
        yield (), await self._fetch_array(self.config.entry_url, client)

    def _discovery_result(self, identifier: str, record: dict[str, object]) -> JsonLdDiscoveryResult:  # noqa: PLR6301
        return JsonLdDiscoveryResult(identifier=identifier, payload=record, harvest_source_id=identifier)

    def _record_identifier(self, record: dict[str, object]) -> str:  # noqa: PLR6301
        """Build a stable, collision-safe identifier for a JSON-LD record.

        PubPlant JSON array sources may deliberately have several records share
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
