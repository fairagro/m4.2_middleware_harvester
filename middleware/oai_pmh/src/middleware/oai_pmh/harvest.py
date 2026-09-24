"""ListRecords iteration helpers for the OAI-PMH plugin."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING
from xml.etree.ElementTree import ParseError, tostring

from defusedxml.ElementTree import fromstring  # type: ignore[import-untyped]

from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.oai_pmh.client import RateLimiter, create_scythe
from middleware.oai_pmh.config import Config
from middleware.oai_pmh.errors import OaiPmhProtocolError
from middleware.parsing.discovery import XmlDiscoveryResult

if TYPE_CHECKING:
    from oaipmh_scythe import Scythe
    from oaipmh_scythe.models import Record


def _metadata_xml(record: Record) -> str:
    """Serialize the first child of OAI ``<metadata>`` as Unicode XML via defusedxml."""
    identifier = record.header.identifier or "unknown"
    try:
        root = fromstring(record.raw)
    except ParseError as exc:
        raise RecordProcessingError(
            f"OAI record XML unparseable: {identifier}: {exc}",
            identifier,
            exc,
        ) from exc

    metadata_element = root.find(".//{*}metadata")
    if metadata_element is None:
        raise RecordProcessingError(
            f"OAI record missing <metadata>: {identifier}",
            identifier,
        )
    children = list(metadata_element)
    if not children:
        raise RecordProcessingError(
            f"OAI record has empty <metadata>: {identifier}",
            identifier,
        )
    payload = tostring(children[0], encoding="unicode")
    if not isinstance(payload, str):
        raise TypeError("expected str from ElementTree.tostring")
    return payload


def _set_scopes(config: Config) -> list[str | None]:
    """Return ListRecords ``set_`` arguments: ``[None]`` when unfiltered."""
    if not config.sets:
        return [None]
    return list(config.sets)


def iter_discovery_units(
    config: Config,
    *,
    scythe: Scythe | None = None,
    rate_limiter: RateLimiter | None = None,
) -> Iterator[XmlDiscoveryResult | SkippedRecord | RecordProcessingError]:
    """Yield discovery units / skips / record errors from ListRecords (sync)."""
    owns_client = scythe is None
    client = scythe or create_scythe(config)
    limiter = rate_limiter or RateLimiter(config.max_requests_per_second)
    try:
        for set_spec in _set_scopes(config):
            limiter.wait()
            try:
                records = client.list_records(
                    metadata_prefix=config.metadata_prefix,
                    set_=set_spec,
                    ignore_deleted=False,
                )
            except Exception as exc:  # noqa: BLE001
                scope = f" set={set_spec!r}" if set_spec is not None else ""
                raise OaiPmhProtocolError(f"ListRecords failed for {config.endpoint_url}{scope}: {exc}") from exc

            for item in records:
                # Scythe may yield OAIResponse between pages; only Records carry headers.
                if not hasattr(item, "header"):
                    continue
                record: Record = item  # type: ignore[assignment]
                identifier = record.header.identifier or "unknown"
                if record.deleted or record.header.deleted:
                    yield SkippedRecord(
                        f"OAI record deleted: {identifier}",
                        identifier,
                    )
                    continue
                try:
                    xml = _metadata_xml(record)
                except RecordProcessingError as exc:
                    yield exc
                    continue
                yield XmlDiscoveryResult(identifier=identifier, xml=xml)
    finally:
        if owns_client:
            client.close()
