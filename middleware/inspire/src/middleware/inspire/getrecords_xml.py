"""GetRecords XML helpers for CSW paging (kept out of ``csw_client`` for line budget)."""

from __future__ import annotations

import logging

import lxml.etree  # type: ignore[import-untyped]

from middleware.inspire.xml_hardening import HARDENED_XML_PARSER

logger = logging.getLogger(__name__)

_CSW_NS = "http://www.opengis.net/cat/csw/2.0.2"
_CSW_GET_RECORDS_TAG = f"{{{_CSW_NS}}}GetRecords"
_ISO_OUTPUT_SCHEMA = "http://www.isotc211.org/2005/gmd"


def normalize_xml_query(xml_query: str | bytes) -> str | bytes:
    """Normalize raw XML queries for OWSLib compatibility."""
    if isinstance(xml_query, str) and ("<?xml" in xml_query and "encoding" in xml_query):
        return xml_query.encode("utf-8")
    return xml_query


def find_get_records_element(root: lxml.etree._Element) -> lxml.etree._Element | None:
    """Return *root* when it is a CSW 2.0.2 GetRecords element; otherwise None.

    Only the document root is accepted. The element must expand to the CSW 2.0.2
    namespace (any prefix or default xmlns is fine); unnamespaced ``GetRecords``
    and GetRecords in any other namespace are rejected.
    """
    if root.tag == _CSW_GET_RECORDS_TAG:
        return root
    return None


def serialize_xml_query(root: lxml.etree._Element, as_bytes: bool) -> str | bytes:
    """Serialize a GetRecords element for OWSLib."""
    if as_bytes:
        payload = lxml.etree.tostring(root, encoding="UTF-8", xml_declaration=True)
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError("expected bytes from lxml.etree.tostring")
        return bytes(payload)
    payload = lxml.etree.tostring(root, encoding="unicode")
    if not isinstance(payload, str):
        raise TypeError("expected str from lxml.etree.tostring")
    return payload


def apply_xml_paging_attrs(root: lxml.etree._Element, batch_size: int, start_position: int) -> None:
    """Set CSW paging attributes on a GetRecords root (in-place)."""
    root.set("startPosition", str(start_position))
    root.set("maxRecords", str(batch_size))


def _coerce_attr_int(value: object) -> int | None:
    """Coerce a GetRecords attribute value to int when possible."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, list) and value:
        return _coerce_attr_int(value[0])
    return None


def prepare_xml_paging(xml_query: str | bytes, chunk_size: int) -> tuple[lxml.etree._Element, int, int, bool]:
    """Parse GetRecords XML and resolve page size / initial start overrides.

    Returns:
        (root element, page_size, start_position, serialize_as_bytes)
    """
    normalized = normalize_xml_query(xml_query)
    as_bytes = isinstance(normalized, (bytes, bytearray))
    try:
        root = lxml.etree.fromstring(normalized, parser=HARDENED_XML_PARSER)
    except lxml.etree.XMLSyntaxError as exc:
        raise ValueError(f"xml_query is not well-formed XML: {exc}") from exc

    get_records = find_get_records_element(root)
    if get_records is None:
        raise ValueError("xml_query must have a CSW GetRecords root element")

    page_size = chunk_size
    raw_max = get_records.get("maxRecords")
    if raw_max is not None:
        xml_max = _coerce_attr_int(raw_max)
        if xml_max is not None and xml_max > 0:
            page_size = xml_max
            logger.info("xml_query maxRecords=%s overrides chunk_size for page size", xml_max)
        else:
            logger.warning(
                "xml_query maxRecords=%r is invalid or non-positive; using chunk_size=%s",
                raw_max,
                chunk_size,
            )

    start_position = 1
    raw_start = get_records.get("startPosition")
    if raw_start is not None:
        xml_start = _coerce_attr_int(raw_start)
        if xml_start is not None and xml_start >= 1:
            start_position = xml_start
            if xml_start != 1:
                logger.info("xml_query startPosition=%s overrides initial paging offset", xml_start)
        else:
            logger.warning(
                "xml_query startPosition=%r is invalid or non-positive; using startPosition=1",
                raw_start,
            )

    # Inspect only — request copies apply ISO schema so the shared template stays intact.
    raw_schema = get_records.get("outputSchema")
    if raw_schema is not None and raw_schema != _ISO_OUTPUT_SCHEMA:
        logger.warning(
            "xml_query outputSchema=%r will be overridden to ISO (%s) for harvest parsing",
            raw_schema,
            _ISO_OUTPUT_SCHEMA,
        )

    return get_records, page_size, start_position, as_bytes
