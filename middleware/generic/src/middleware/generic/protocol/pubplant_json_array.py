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
import logging
import re
from collections.abc import AsyncGenerator
from typing import Annotated

from pydantic import ConfigDict, Field

from middleware.contracts.nice_http_client import NiceHttpClient
from middleware.generic.protocol.json_array import JsonArrayProtocol
from middleware.generic.protocol.protocol import Protocol, ProtocolType, ProtocolTypeConfig
from middleware.parsing.discovery import JsonLdDiscoveryResult
from middleware.payload.linked_data_mapper import LinkedDataMapper

logger = logging.getLogger(__name__)

_DOI_LIKE = re.compile(r"\s*10\.\d+/")
_RESOLVER = r"(?:https?://)?(?:(?:dx|www)\.)?doi\.org/"
# Two or more prefixes, or a single one without a scheme (never a valid resolver URL); a lone ``https://doi.org/`` is
# well-formed and stays untouched.
_RESOLVER_STACK = re.compile(rf"(?:{_RESOLVER}){{2,}}|(?:(?:dx|www)\.)?doi\.org/", re.IGNORECASE)


def _is_repairable(key: str, value: object) -> bool:
    if not isinstance(value, str):
        return False
    return key == "@id" or (key == "identifier" and _DOI_LIKE.match(value) is not None)


def _strip_identifier_whitespace(item: object) -> object:
    """Remove whitespace from the top-level ``@id`` and DOI-like ``identifier`` strings of a record.

    PlabiPD ships a few DOIs with a stray space (``10.1038/ s41597-...``); rdflib drops a node
    whose ``@id`` is not a valid IRI. Neither an IRI nor a DOI can contain whitespace, so no valid
    value changes. Any other ``identifier`` is free text and stays as the provider wrote it.
    """
    if not isinstance(item, dict):
        return item
    repaired = {key: "".join(value.split()) if _is_repairable(key, value) else value for key, value in item.items()}
    changed = {key: value for key, value in item.items() if repaired[key] != value}
    if changed:
        logger.warning(
            "PubPlant record has whitespace in its identifier; repaired (%s)",
            ", ".join(f"{key}={value!r}" for key, value in changed.items()),
        )
    return repaired


def _collapse_resolver_stack(value: object) -> str | None:
    """Return the bare DOI behind a stack of ``doi.org`` resolver prefixes, or None if there is none to collapse."""
    if not isinstance(value, str):
        return None
    match = _RESOLVER_STACK.match(value)
    if match is None:
        return None
    doi = value[match.end() :]
    return doi if _DOI_LIKE.match(doi) else None


def _collapse_doubled_resolver(item: object) -> object:
    """Collapse a stack of DOI resolver prefixes in the top-level ``@id`` and ``identifier`` of a record.

    PlabiPD ships one record with ``@id`` ``https://doi.org/doi.org/10.…`` and ``identifier``
    ``doi.org/10.…``; ``normalize_doi`` strips the resolver once and rejects what is left.
    ``@id`` becomes ``https://doi.org/<doi>`` and ``identifier`` the bare ``<doi>``.
    """
    if not isinstance(item, dict):
        return item
    repaired = dict(item)
    if (doi := _collapse_resolver_stack(item.get("@id"))) is not None:
        repaired["@id"] = f"https://doi.org/{doi}"
    if (doi := _collapse_resolver_stack(item.get("identifier"))) is not None:
        repaired["identifier"] = doi
    changed = {key: value for key, value in item.items() if repaired[key] != value}
    if changed:
        logger.warning(
            "PubPlant record has a doubled DOI resolver; repaired (%s)",
            ", ".join(f"{key}={value!r}" for key, value in changed.items()),
        )
    return repaired


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
        yield (
            (),
            [
                _collapse_doubled_resolver(_strip_identifier_whitespace(item))
                for item in await self._fetch_array(self.config.entry_url, client)
            ],
        )

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
