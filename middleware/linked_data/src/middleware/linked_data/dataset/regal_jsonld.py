"""Regal JSON-LD dataset implementation (inline discovery payloads)."""

from __future__ import annotations

import asyncio
import json
import logging

from rdflib import Graph

from middleware.harvester.nice_http_client import NiceHttpClient

from ..config import Config, DatasetType
from ..errors import LinkedDataDatasetError
from .dataset import Dataset, DiscoveryResult, JsonLdDiscoveryResult

logger = logging.getLogger(__name__)


@Dataset.register(DatasetType.regal_jsonld)
class RegalJsonLdDataset(Dataset):
    """Dataset wrapper for inline Regal JSON-LD records (no HTTP fetch)."""

    def __init__(self, identifier: str, payload: dict[str, object], config: Config) -> None:
        """Initialize with the stable record identifier and JSON-LD payload."""
        self._identifier = identifier
        self._payload = payload
        self._config = config

    @property
    def identifier(self) -> str:
        """Return the stable Regal record identifier."""
        return self._identifier

    @classmethod
    def from_discovery_result(
        cls,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: Config,
    ) -> Dataset:
        """Construct a RegalJsonLdDataset from an inline JSON-LD discovery result."""
        del client  # Regal payloads are inline; HTTP access is unused.
        if not isinstance(discovery_result, JsonLdDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")
        return cls(discovery_result.identifier, discovery_result.payload, config)

    async def to_graph(self) -> Graph:
        """Parse the inline Regal JSON-LD payload into an rdflib Graph."""
        payload = self._normalize_payload(self._payload, self._config.effective_resource_base_url)
        payload_bytes = json.dumps(payload).encode("utf-8")
        try:
            if len(payload_bytes) >= self._config.jsonld_parse_threshold_bytes:
                return await asyncio.to_thread(self._parse_jsonld, payload_bytes)
            return self._parse_jsonld(payload_bytes)
        except LinkedDataDatasetError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise LinkedDataDatasetError(f"Failed to parse Regal JSON-LD for {self._identifier}: {exc}") from exc

    @staticmethod
    def _normalize_payload(payload: dict[str, object], resource_base_url: str) -> dict[str, object]:
        """Return a copy with a resolvable @id for stable RDF subjects.

        Compact Regal ids such as ``frl:123`` are expanded to
        ``{resource_base_url}frl:123`` so rdflib gets an absolute IRI.
        """
        normalized = dict(payload)
        record_id = normalized.get("@id")
        if isinstance(record_id, str) and record_id.strip() and "://" not in record_id:
            normalized["@id"] = f"{resource_base_url}{record_id.strip()}"
        return normalized

    @staticmethod
    def _parse_jsonld(payload_bytes: bytes) -> Graph:
        graph = Graph()
        try:
            graph.parse(data=payload_bytes, format="json-ld")
        except Exception as exc:  # noqa: BLE001
            raise LinkedDataDatasetError(f"Invalid Regal JSON-LD payload: {exc}") from exc
        return graph
