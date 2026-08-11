"""CSW client for harvesting INSPIRE metadata records."""

import asyncio
import contextlib
import copy
import logging
import random
from collections.abc import AsyncGenerator, Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TypeVar
from urllib.parse import urlencode

import lxml.etree  # type: ignore[import-untyped]
from owslib.catalogue.csw2 import CatalogueServiceWeb  # type: ignore[import-untyped]
from owslib.fes import OgcExpression  # type: ignore[import-untyped]
from owslib.iso import MD_Metadata  # type: ignore[import-untyped]
from owslib.util import Authentication  # type: ignore[import-untyped]

from middleware.harvester.errors import RecordProcessingError

from .config import Config
from .errors import CswConnectionError
from .iso_parser import IsoParser
from .models import InspireRecord

T = TypeVar("T")

logger = logging.getLogger(__name__)

_CSW_NS = "http://www.opengis.net/cat/csw/2.0.2"
_CSW_GET_RECORDS_TAG = f"{{{_CSW_NS}}}GetRecords"
_ISO_OUTPUT_SCHEMA = "http://www.isotc211.org/2005/gmd"
_DC_OUTPUT_SCHEMA = "http://www.opengis.net/cat/csw/2.0.2"


class CSWClient:
    """Client for harvesting metadata from a CSW endpoint."""

    def __init__(self, config: Config) -> None:
        """Initialize the CSWClient from a Config object.

        Args:
            config: Plugin configuration holding the CSW URL, timeout, and query options.
        """
        self._config = config
        self._csw: CatalogueServiceWeb | None = None
        self._parser = IsoParser()
        self._executor: ThreadPoolExecutor | None = None

    def _connect(self) -> None:
        """Connect to the CSW service without error wrapping."""
        logger.debug(
            "Attempting CSW connection to %s with timeout=%s and user_agent=%s",
            self._config.csw_url,
            self._config.timeout,
            self._config.user_agent,
        )
        if self._config.verify_ssl is False:
            logger.warning(
                "TLS certificate verification is disabled for CSW endpoint %s",
                self._config.csw_url,
            )
        self._csw = CatalogueServiceWeb(
            self._config.csw_url,
            timeout=self._config.timeout,
            headers={"User-Agent": self._config.user_agent},
            auth=Authentication(verify=self._config.verify_ssl),
        )
        csw_title = None
        if self._csw and hasattr(self._csw, "identification") and self._csw.identification:
            csw_title = getattr(self._csw.identification, "title", None)
        logger.info("Connected to CSW at %s: %s", self._config.csw_url, csw_title)

    def connect(self) -> None:
        """Connect to the CSW service."""
        try:
            self._connect()
        except (OSError, TimeoutError, ValueError) as e:
            logger.error(
                "Failed to connect to CSW at %s: %s",
                self._config.csw_url,
                e,
            )
            logger.debug(
                "Failed to connect to CSW at %s with timeout=%s.",
                self._config.csw_url,
                self._config.timeout,
                exc_info=e,
            )
            raise CswConnectionError(f"Failed to connect to CSW at {self._config.csw_url}: {e}") from e

    def get_executor(self) -> ThreadPoolExecutor:
        """Return the per-client executor, creating it lazily on first use."""
        return self._get_executor()

    def _get_executor(self) -> ThreadPoolExecutor:
        """Return the per-client executor, creating it lazily on first use."""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self._config.csw_thread_pool_size)
        return self._executor

    def _shutdown_executor(self) -> None:
        """Shut down the owned executor if it exists."""
        if self._executor is None:
            return
        executor = self._executor
        self._executor = None
        executor.shutdown(wait=False)

    async def __aenter__(self) -> "CSWClient":
        """Prepare the executor and return the active CSWClient."""
        self._get_executor()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: object | None
    ) -> None:
        """Shut down the owned executor when exiting the async context."""
        self._shutdown_executor()

    def __del__(self) -> None:
        """Best-effort finalizer: keep minimal and avoid complex logic."""
        with contextlib.suppress(Exception):
            self._shutdown_executor()

    async def _run_in_executor(self, fn: Callable[..., T], *args: object, **kwargs: object) -> T:
        """Run a function in the owned executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._get_executor(), fn, *args, **kwargs)

    def get_record_url(self, record_id: str) -> str:
        """
        Construct a URL to fetch a single record in ISO 19139 format.

        Args:
            record_id: The identifier of the record.

        Returns:
            The CSW GetRecordById URL.
        """
        params = {
            "service": "CSW",
            "version": "2.0.2",
            "request": "GetRecordById",
            "id": record_id,
            "outputSchema": "http://www.isotc211.org/2005/gmd",
            "elementSetName": "full",
        }
        # Handle base URL that might already contain query parameters
        base = self._config.csw_url.rstrip("?")
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}{urlencode(params)}"

    def _resolve_filter(
        self,
        cql_query: str | None,
        xml_query: str | bytes | None,
        fes_constraints: list[OgcExpression] | None,
    ) -> tuple[str | bytes | None, list[OgcExpression] | None, str | None]:
        """Resolve effective filter values, merging call-site args with Config defaults.

        Config provides defaults for ``xml_query`` and ``cql_query`` only.
        ``fes_constraints`` has no Config equivalent (OWSLib objects are not YAML-serializable).

        Returns:
            (effective_xml, effective_fes, effective_cql) — at most one is non-None.

        Raises:
            ValueError: If more than one filter type would be active simultaneously.
        """
        effective_xml = xml_query if xml_query is not None else self._config.xml_query
        effective_fes = fes_constraints
        effective_cql = cql_query if cql_query is not None else self._config.cql_query

        active = [
            ("xml_query", effective_xml),
            ("fes_constraints", effective_fes),
            ("cql_query", effective_cql),
        ]
        active_names = [name for name, val in active if val]
        if len(active_names) > 1:
            raise ValueError(
                f"Conflicting query parameters: {', '.join(active_names)}. "
                "CSW 2.0.2 allows only one filter type per request. "
                "Provide at most one of xml_query, fes_constraints, or cql_query."
            )

        return effective_xml, effective_fes, effective_cql

    def get_records(
        self,
        cql_query: str | None = None,
        xml_query: str | bytes | None = None,
        fes_constraints: list[OgcExpression] | None = None,
        chunk_size: int | None = None,
        max_records: int | None = None,
    ) -> Iterator[InspireRecord | RecordProcessingError]:
        """Retrieve records from the CSW, yielding InspireRecord or RecordProcessingError objects.

        Exactly one filter mode may be active at a time (including values inherited from Config):
          - xml_query       — raw GetRecords XML; paginated (paging attrs rewritten per page)
          - fes_constraints — OWSLib FES constraint objects; paginated
          - cql_query       — CQL text query string; paginated
          - (none)          — fetch all records; paginated

        Combining more than one raises ``ValueError``, because CSW 2.0.2 allows only one
        filter type per request and OWSLib silently ignores the lower-priority one.

        Explicit arguments override the corresponding Config fields.
        chunk_size and max_records fall back to Config values when not provided.
        For ``xml_query``, a valid XML ``maxRecords`` overrides page size (chunk_size);
        a valid XML ``startPosition`` overrides the initial offset. Config ``max_records``
        remains the harvest-wide cap for all modes.

        Args:
            cql_query: CQL filter string, e.g. "AnyText LIKE '%agriculture%'". Overrides
                       config.cql_query when provided.
            xml_query: Raw GetRecords XML body. Overrides config.xml_query when provided.
            fes_constraints: List of OWSLib FES constraint objects (e.g. PropertyIsLike).
            chunk_size: Records per paginated request. Overrides config.chunk_size when provided.
            max_records: Maximum records to harvest (None = all). Overrides config.max_records.

        Raises:
            ValueError: If more than one filter mode is active simultaneously.
        """
        effective_xml, effective_fes, effective_cql = self._resolve_filter(cql_query, xml_query, fes_constraints)
        effective_chunk_size = chunk_size if chunk_size is not None else self._config.chunk_size
        effective_max_records = max_records if max_records is not None else self._config.max_records
        # Spec: invalid GetRecords must raise before any network call (including connect).
        prepared_xml = self._prepare_xml_query_before_network(effective_xml, effective_chunk_size)

        if self._csw is None:
            self.connect()
        if self._csw is None:
            raise RuntimeError("CSW client is not initialized.")

        if prepared_xml is not None:
            yield from self._get_records_by_xml_prepared(prepared_xml, effective_max_records)
        elif effective_fes is not None:
            yield from self._get_records_by_fes(effective_fes, effective_chunk_size, effective_max_records)
        elif effective_cql is not None:
            yield from self._get_records_by_cql(effective_cql, effective_chunk_size, effective_max_records)
        else:
            yield from self._get_records_standard(effective_chunk_size, effective_max_records)

    async def get_records_async(
        self,
        cql_query: str | None = None,
        xml_query: str | bytes | None = None,
        fes_constraints: list[OgcExpression] | None = None,
        chunk_size: int | None = None,
        max_records: int | None = None,
    ) -> AsyncGenerator[InspireRecord | RecordProcessingError, None]:
        """Asynchronously retrieve records from the CSW by offloading blocking OWSLib calls."""
        effective_xml, effective_fes, effective_cql = self._resolve_filter(cql_query, xml_query, fes_constraints)
        effective_chunk_size = chunk_size if chunk_size is not None else self._config.chunk_size
        effective_max_records = max_records if max_records is not None else self._config.max_records
        # Spec: invalid GetRecords must raise before any network call (including connect).
        prepared_xml = self._prepare_xml_query_before_network(effective_xml, effective_chunk_size)

        if self._csw is None:
            await self._retry_async(self._connect, "connect")
        if self._csw is None:
            raise RuntimeError("CSW client is not initialized.")

        strategy: tuple[str, Callable[..., Iterator[InspireRecord | RecordProcessingError]], tuple[object, ...]]
        if prepared_xml is not None:
            strategy = (
                "get_records_by_xml",
                self._get_records_by_xml_prepared,
                (prepared_xml, effective_max_records),
            )
        else:
            strategy = self._pick_strategy(
                effective_xml, effective_fes, effective_cql, effective_chunk_size, effective_max_records
            )
        name, fn, args = strategy
        records = await self._retry_async(self._iter_to_list, name, fn, *args)
        for item in records:
            yield item

    def _pick_strategy(
        self,
        effective_xml: str | bytes | None,
        effective_fes: list[OgcExpression] | None,
        effective_cql: str | None,
        effective_chunk_size: int,
        effective_max_records: int | None,
    ) -> tuple[str, Callable[..., Iterator[InspireRecord | RecordProcessingError]], tuple[object, ...]]:
        """Return (strategy_name, callable, args) for the active filter mode."""
        if effective_xml:
            return (
                "get_records_by_xml",
                self._get_records_by_xml,
                (effective_xml, effective_chunk_size, effective_max_records),
            )
        if effective_fes:
            return (
                "get_records_by_fes",
                self._get_records_by_fes,
                (
                    effective_fes,
                    effective_chunk_size,
                    effective_max_records,
                ),
            )
        if effective_cql:
            return (
                "get_records_by_cql",
                self._get_records_by_cql,
                (
                    effective_cql,
                    effective_chunk_size,
                    effective_max_records,
                ),
            )
        return "get_records_standard", self._get_records_standard, (effective_chunk_size, effective_max_records)

    @staticmethod
    def _iter_to_list(
        fn: Callable[..., Iterator[InspireRecord | RecordProcessingError]],
        *args: object,
    ) -> list[InspireRecord | RecordProcessingError]:
        """Convert any record-iterator callable to a list (used by _retry_async)."""
        return list(fn(*args))

    def _get_records_by_cql(
        self, cql_query: str, chunk_size: int, max_records: int | None
    ) -> Iterator[InspireRecord | RecordProcessingError]:
        """Retrieve records using a CQL text query with pagination."""
        logger.info("Using CQL query for harvesting: %s", cql_query)
        yield from self._get_records_paged(chunk_size, cql_query, None, max_records)

    def _normalize_xml_query(self, xml_query: str | bytes) -> str | bytes:
        """Normalize raw XML queries for OWSLib compatibility."""
        if isinstance(xml_query, str) and ("<?xml" in xml_query and "encoding" in xml_query):
            return xml_query.encode("utf-8")
        return xml_query

    def _prepare_xml_query_before_network(
        self, xml_query: str | bytes | None, chunk_size: int
    ) -> tuple[lxml.etree._Element, int, int, bool] | None:
        """Parse/validate ``xml_query`` before connect; return prepared paging state or None."""
        if xml_query is None:
            return None
        return self._prepare_xml_paging(xml_query, chunk_size)

    def _get_records_by_xml(
        self, xml_query: str | bytes, chunk_size: int, max_records: int | None
    ) -> Iterator[InspireRecord | RecordProcessingError]:
        """Retrieve records using a GetRecords XML body with pagination."""
        logger.info("Using XML GetRecords request for harvesting (paginated).")
        yield from self._get_records_paged(chunk_size, None, None, max_records, xml=xml_query)

    def _get_records_by_xml_prepared(
        self,
        prepared_xml: tuple[lxml.etree._Element, int, int, bool],
        max_records: int | None,
    ) -> Iterator[InspireRecord | RecordProcessingError]:
        """Paginate using XML already validated/prepared before connect."""
        logger.info("Using XML GetRecords request for harvesting (paginated).")
        page_size = prepared_xml[1]
        yield from self._get_records_paged(page_size, None, None, max_records, xml=prepared_xml)

    def _get_records_by_fes(
        self, fes_constraints: list[OgcExpression], chunk_size: int, max_records: int | None
    ) -> Iterator[InspireRecord | RecordProcessingError]:
        """Retrieve records using FES constraints with pagination."""
        logger.info("Using FES constraints for harvesting.")
        yield from self._get_records_paged(chunk_size, None, fes_constraints, max_records)

    def _get_records_standard(
        self, chunk_size: int, max_records: int | None
    ) -> Iterator[InspireRecord | RecordProcessingError]:
        """Retrieve records using standard paged harvesting."""
        yield from self._get_records_paged(chunk_size, None, None, max_records)

    def _get_records_paged(
        self,
        chunk_size: int,
        cql_query: str | None,
        fes_constraints: list[OgcExpression] | None,
        max_records: int | None,
        xml: str | bytes | tuple[lxml.etree._Element, int, int, bool] | None = None,
    ) -> Iterator[InspireRecord | RecordProcessingError]:
        """Retrieve all records using pagination, fetching chunk_size records per request.

        CSW 2.0.2 ``startPosition`` is 1-based. Starting at 0 (OWSLib default) makes
        servers treat the first page as position 1, then ``start += page_size`` requests
        position ``page_size`` again and duplicates one record per page boundary.

        When ``xml`` is set, the GetRecords filter body is preserved and only paging
        attributes are rewritten. Pass prepared paging state from
        ``_prepare_xml_query_before_network`` so invalid XML fails before ``connect()``.
        """
        start_position = 1
        effective_chunk_size = chunk_size
        xml_page: tuple[lxml.etree._Element, bool] | None = None
        if isinstance(xml, tuple):
            xml_root, effective_chunk_size, start_position, xml_as_bytes = xml
            xml_page = (xml_root, xml_as_bytes)
        elif xml is not None:
            xml_root, effective_chunk_size, start_position, xml_as_bytes = self._prepare_xml_paging(xml, chunk_size)
            xml_page = (xml_root, xml_as_bytes)

        records_yielded = 0

        while True:
            page = self._fetch_and_parse_page(
                effective_chunk_size,
                start_position,
                cql_query,
                fes_constraints,
                xml_page,
            )
            if page is None:
                break

            results, count = page
            fetched_batch_size = len(results)
            results, count = self._limit_page_to_max_records(results, count, records_yielded, max_records)
            if not results:
                break

            yield from results
            records_yielded += count

            if max_records is not None and records_yielded >= max_records:
                break

            # Use the fetched page size, not a max_records-trimmed yield list, so the
            # missing-nextrecord/returned fallback advances by the real CSW batch length.
            next_start = self._advance_start_position(start_position, records_in_batch=fetched_batch_size)
            if next_start is None:
                break
            start_position = next_start

    @staticmethod
    def _limit_page_to_max_records(
        results: list[InspireRecord | RecordProcessingError],
        count: int,
        records_yielded: int,
        max_records: int | None,
    ) -> tuple[list[InspireRecord | RecordProcessingError], int]:
        """Trim a page so successful records do not exceed the remaining max_records budget.

        ``RecordProcessingError`` items are never capped: every error from the fetched page
        is kept so data-quality failures remain visible even when the success budget is full.
        """
        if max_records is None:
            return results, count
        remaining = max_records - records_yielded
        if remaining <= 0:
            # Success budget already exhausted — still surface parse errors from this page.
            return [item for item in results if isinstance(item, RecordProcessingError)], 0
        if count <= remaining:
            return results, count

        limited: list[InspireRecord | RecordProcessingError] = []
        successes = 0
        for item in results:
            if isinstance(item, RecordProcessingError):
                limited.append(item)
                continue
            if successes >= remaining:
                continue
            limited.append(item)
            successes += 1
        return limited, successes

    def _fetch_and_parse_page(
        self,
        batch_size: int,
        start_position: int,
        cql_query: str | None,
        fes_constraints: list[OgcExpression] | None,
        xml_page: tuple[lxml.etree._Element, bool] | None,
    ) -> tuple[list[InspireRecord | RecordProcessingError], int] | None:
        """Fetch one CSW page and parse it; return None when the page is empty or fetch fails."""
        if xml_page is not None:
            xml_root, xml_as_bytes = xml_page
            iso_ok = self._fetch_iso_batch_xml(xml_root, batch_size, start_position, xml_as_bytes)
        else:
            iso_ok = self._fetch_iso_batch(batch_size, start_position, cql_query, fes_constraints)
        if not iso_ok:
            return None

        results, errors_without_id, count = self._parse_iso_batch()
        if not results:
            return None

        if errors_without_id:
            if xml_page is not None:
                xml_root, xml_as_bytes = xml_page
                dc_ids = self._fetch_dc_ids_xml(xml_root, batch_size, start_position, xml_as_bytes)
            else:
                dc_ids = self._fetch_dc_ids(batch_size, start_position, cql_query, fes_constraints)
            self._apply_dc_fallback(results, errors_without_id, dc_ids)

        return results, count

    def _advance_start_position(self, start_position: int, records_in_batch: int) -> int | None:
        """Return the next page start, or None when pagination is complete or stuck."""
        next_start = self._next_start_position(start_position, records_in_batch=records_in_batch)
        if next_start is None:
            return None
        if next_start <= start_position:
            logger.warning(
                "CSW pagination did not advance (startPosition=%s, next=%s); stopping.",
                start_position,
                next_start,
            )
            return None
        if self._all_records_fetched(next_start):
            return None
        return next_start

    def _prepare_xml_paging(
        self, xml_query: str | bytes, chunk_size: int
    ) -> tuple[lxml.etree._Element, int, int, bool]:
        """Parse GetRecords XML and resolve page size / initial start overrides.

        Returns:
            (root element, page_size, start_position, serialize_as_bytes)
        """
        normalized = self._normalize_xml_query(xml_query)
        as_bytes = isinstance(normalized, (bytes, bytearray))
        try:
            root = lxml.etree.fromstring(normalized)
        except lxml.etree.XMLSyntaxError as exc:
            raise ValueError(f"xml_query is not well-formed XML: {exc}") from exc

        get_records = self._find_get_records_element(root)
        if get_records is None:
            raise ValueError("xml_query must have a CSW GetRecords root element")

        page_size = chunk_size
        raw_max = get_records.get("maxRecords")
        if raw_max is not None:
            xml_max = self._coerce_result_int(raw_max)
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
            xml_start = self._coerce_result_int(raw_start)
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

    @staticmethod
    def _find_get_records_element(root: lxml.etree._Element) -> lxml.etree._Element | None:
        """Return *root* when it is a CSW 2.0.2 GetRecords element; otherwise None.

        Only the document root is accepted. The element must expand to the CSW 2.0.2
        namespace (any prefix or default xmlns is fine); unnamespaced ``GetRecords``
        and GetRecords in any other namespace are rejected.
        """
        if root.tag == _CSW_GET_RECORDS_TAG:
            return root
        return None

    @staticmethod
    def _serialize_xml_query(root: lxml.etree._Element, as_bytes: bool) -> str | bytes:
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

    def _apply_xml_paging_attrs(self, root: lxml.etree._Element, batch_size: int, start_position: int) -> None:
        """Set CSW paging attributes on a GetRecords root (in-place)."""
        root.set("startPosition", str(start_position))
        root.set("maxRecords", str(batch_size))

    def _fetch_iso_batch_xml(
        self,
        xml_root: lxml.etree._Element,
        batch_size: int,
        start_position: int,
        as_bytes: bool,
    ) -> bool:
        """Fetch one ISO page without mutating the shared xml_query template.

        Paging attributes and ISO ``outputSchema`` are applied on a deep copy so the
        operator template (filter body and original attributes) stays intact across pages.
        Transient ``OSError``/``TimeoutError`` are wrapped as ``CswConnectionError`` so the
        async retry layer can retry. ``ValueError`` propagates unwrapped (not retryable).
        """
        if self._csw is None:
            self.connect()
        if self._csw is None:
            raise RuntimeError("CSW client is not initialized.")

        request_root = copy.deepcopy(xml_root)
        self._apply_xml_paging_attrs(request_root, batch_size, start_position)
        # Same as _fetch_iso_batch: ISO parsing only yields MD_Metadata for gmd schema.
        if request_root.get("outputSchema") != _ISO_OUTPUT_SCHEMA:
            request_root.set("outputSchema", _ISO_OUTPUT_SCHEMA)

        try:
            self._csw.getrecords2(xml=self._serialize_xml_query(request_root, as_bytes))
            return True
        except (OSError, TimeoutError) as e:
            # ValueError (e.g. malformed request) is not caught here and propagates
            # unwrapped so the async retry layer does not treat it as transient.
            logger.error("Failed to fetch ISO records from CSW at position %d: %s", start_position, e)
            raise CswConnectionError(f"Failed to fetch ISO records from CSW: {e}") from e

    def _fetch_dc_ids_xml(
        self,
        xml_root: lxml.etree._Element,
        batch_size: int,
        start_position: int,
        as_bytes: bool,
    ) -> list[str]:
        """Fetch DC identifiers for a page using a mutated copy of the xml_query template."""
        if self._csw is None:
            self.connect()
        if self._csw is None:
            raise RuntimeError("CSW client is not initialized.")

        try:
            dc_root = copy.deepcopy(xml_root)
            self._apply_xml_paging_attrs(dc_root, batch_size, start_position)
            dc_root.set("outputSchema", _DC_OUTPUT_SCHEMA)
            for element_set in dc_root.iter():
                if isinstance(element_set.tag, str) and lxml.etree.QName(element_set).localname == "ElementSetName":
                    element_set.text = "brief"
                    break
            self._csw.getrecords2(xml=self._serialize_xml_query(dc_root, as_bytes))
            return [rec.identifier for rec in self._csw.records.values()]
        except (OSError, TimeoutError, ValueError) as e:
            logger.warning("Failed to fetch DC IDs for XML batch at %d: %s", start_position, e)
            return []

    def _next_start_position(self, current_start: int, records_in_batch: int | None = None) -> int | None:
        """Return the next 1-based CSW startPosition, or None when pagination is complete.

        Prefers ``nextrecord`` from the last GetRecords response (0 means no more
        records). Falls back to ``current_start + returned``, then to
        ``current_start + records_in_batch`` when ``matches`` still indicates
        unread records (broken/incomplete CSW result metadata).
        """
        if self._csw is None:
            return None

        nextrecord = self._coerce_result_int(self._csw.results.get("nextrecord"))
        if nextrecord is not None:
            if nextrecord <= 0:
                return None
            return nextrecord

        returned = self._coerce_result_int(self._csw.results.get("returned"))
        if returned is not None and returned > 0:
            return current_start + returned

        batch_len = records_in_batch
        if batch_len is None and self._csw.records:
            batch_len = len(self._csw.records)
        matches = self._coerce_result_int(self._csw.results.get("matches"))
        if isinstance(batch_len, int) and batch_len > 0 and matches is not None:
            next_start = current_start + batch_len
            if next_start <= matches:
                logger.warning(
                    "CSW response missing nextrecord/returned; advancing by batch length %s "
                    "to startPosition %s (matches=%s).",
                    batch_len,
                    next_start,
                    matches,
                )
                return next_start

        return None

    @staticmethod
    def _coerce_result_int(value: object) -> int | None:
        """Coerce OWSLib result metadata values to int when possible."""
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
            return CSWClient._coerce_result_int(value[0])
        return None

    def _parse_iso_batch(
        self,
    ) -> tuple[list[InspireRecord | RecordProcessingError], list[tuple[int, RecordProcessingError]], int]:
        """Parse the last-fetched ISO batch into results, identifier-less errors, and a success count."""
        results: list[InspireRecord | RecordProcessingError] = []
        errors_without_id: list[tuple[int, RecordProcessingError]] = []
        count = 0
        for item in self._yield_iso_records():
            if isinstance(item, RecordProcessingError) and item.record_id.startswith("owslib_random_"):
                errors_without_id.append((len(results), item))
            results.append(item)
            if not isinstance(item, RecordProcessingError):
                count += 1
        return results, errors_without_id, count

    def _apply_dc_fallback(
        self,
        results: list[InspireRecord | RecordProcessingError],
        errors_without_id: list[tuple[int, RecordProcessingError]],
        dc_ids: list[str],
    ) -> None:
        """Enrich identifier-less parse errors with stable DC identifiers (in-place)."""
        if not dc_ids:
            return
        successful_ids: set[str] = {item.identifier for item in results if isinstance(item, InspireRecord)}
        unmatched_dc_ids = [dc_id for dc_id in dc_ids if dc_id not in successful_ids]
        for i, (pos, error) in enumerate(errors_without_id):
            if i >= len(unmatched_dc_ids):
                break
            cause = error.__cause__
            if not isinstance(cause, Exception):
                cause = None
            results[pos] = RecordProcessingError(
                error.args[0] if error.args else str(error),
                unmatched_dc_ids[i],
                original_error=cause,
                url=error.url,
            )

    def _fetch_dc_ids(
        self,
        batch_size: int,
        start_position: int,
        cql_query: str | None,
        fes_constraints: list[OgcExpression] | None,
    ) -> list[str]:
        """Fetch stable identifiers using Dublin Core schema (lazy fallback for broken ISO records)."""
        if self._csw is None:
            self.connect()
        if self._csw is None:
            raise RuntimeError("CSW client is not initialized.")

        try:
            kwargs: dict = {
                "maxrecords": batch_size,
                "startposition": start_position,
                "esn": "brief",
            }
            if fes_constraints:
                self._csw.getrecords2(constraints=fes_constraints, **kwargs)
            elif cql_query:
                self._csw.getrecords2(cql=cql_query, **kwargs)
            else:
                self._csw.getrecords2(**kwargs)

            return [rec.identifier for rec in self._csw.records.values()]
        except (OSError, TimeoutError, ValueError) as e:
            logger.warning("Failed to fetch DC IDs for batch at %d: %s", start_position, e)
            return []

    def _fetch_iso_batch(
        self,
        batch_size: int,
        start_position: int,
        cql_query: str | None,
        fes_constraints: list[OgcExpression] | None,
    ) -> bool:
        """Fetch a batch of records in ISO 19139 format.

        Transient ``OSError``/``TimeoutError`` are wrapped as ``CswConnectionError`` so the
        async retry layer can retry. ``ValueError`` propagates unwrapped (not retryable).
        """
        if self._csw is None:
            self.connect()
        if self._csw is None:
            raise RuntimeError("CSW client is not initialized.")

        try:
            kwargs: dict = {
                "maxrecords": batch_size,
                "startposition": start_position,
                "esn": "full",
                "outputschema": "http://www.isotc211.org/2005/gmd",
            }
            if fes_constraints:
                self._csw.getrecords2(constraints=fes_constraints, **kwargs)
            elif cql_query:
                self._csw.getrecords2(cql=cql_query, **kwargs)
            else:
                self._csw.getrecords2(**kwargs)
            return True
        except (OSError, TimeoutError) as e:
            # ValueError (e.g. malformed request) is not caught here and propagates
            # unwrapped so the async retry layer does not treat it as transient.
            logger.error("Failed to fetch ISO records from CSW at position %d: %s", start_position, e)
            raise CswConnectionError(f"Failed to fetch ISO records from CSW: {e}") from e

    def _yield_iso_records(self) -> Iterator[InspireRecord | RecordProcessingError]:
        """Yield parsed ISO records from the last-fetched batch (ISO-first, no DC involved)."""
        if self._csw is None or not self._csw.records:
            return

        for owslib_id, record in self._csw.records.items():
            if isinstance(record, MD_Metadata):
                iso_id = getattr(record, "identifier", None)
                record_id = iso_id if iso_id and not iso_id.startswith("owslib_random_") else owslib_id
                try:
                    yield self._parse_iso_record(record, record_uuid=record_id)
                except Exception as e:  # noqa: BLE001
                    yield RecordProcessingError(str(e), record_id, original_error=e)

    def _all_records_fetched(self, start_position: int) -> bool:
        """Return True when *start_position* is past the last matching record.

        CSW ``startPosition`` is 1-based, so position ``matches`` is still a
        valid record. Only ``start_position > matches`` means there is nothing
        left to fetch (``>=`` would skip the final record when ``nextrecord``
        equals ``matches``).
        """
        if self._csw is None:
            return True
        matches = self._coerce_result_int(self._csw.results.get("matches"))
        return matches is not None and start_position > matches

    async def get_record_count_async(
        self,
        cql_query: str | None = None,
        xml_query: str | bytes | None = None,
        fes_constraints: list[OgcExpression] | None = None,
    ) -> int:
        """Asynchronously get the total number of matching records with retry."""
        return await self._retry_async(
            self.get_record_count,
            "get_record_count",
            cql_query,
            xml_query,
            fes_constraints,
        )

    def get_record_count(
        self,
        cql_query: str | None = None,
        xml_query: str | bytes | None = None,
        fes_constraints: list[OgcExpression] | None = None,
    ) -> int:
        """Get the total number of matching records without fetching them.

        Uses the same filter resolution and conflict rules as ``get_records``:
        config values for ``cql_query`` / ``xml_query`` are used as defaults, and
        providing more than one filter type raises ``ValueError``.

        Args:
            cql_query: CQL filter string. Overrides config.cql_query when provided.
            xml_query: Raw GetRecords XML body. Overrides config.xml_query when provided.
            fes_constraints: List of OWSLib FES constraint objects.

        Raises:
            ValueError: If more than one filter type is active simultaneously.

        Returns:
            Total number of matching records.
        """
        effective_xml, effective_fes, effective_cql = self._resolve_filter(cql_query, xml_query, fes_constraints)
        # Spec: invalid GetRecords must raise before any network call (including connect).
        self._prepare_xml_query_before_network(effective_xml, self._config.chunk_size)

        if self._csw is None:
            self.connect()
        if self._csw is None:
            return 0

        if effective_xml:
            self._csw.getrecords2(xml=self._normalize_xml_query(effective_xml))
        elif effective_fes:
            self._csw.getrecords2(constraints=effective_fes, maxrecords=1, esn="brief")
        elif effective_cql:
            self._csw.getrecords2(cql=effective_cql, maxrecords=1, esn="brief")
        else:
            self._csw.getrecords2(maxrecords=1, esn="brief")

        matches = self._csw.results.get("matches", 0)
        if isinstance(matches, (int, str)):
            return int(matches)
        if isinstance(matches, list) and matches:
            return int(matches[0])
        return 0

    @staticmethod
    def _is_http_client_error(exc: BaseException) -> bool:
        """Return True if exc is an HTTP 4xx client error (non-retryable)."""
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        return isinstance(status_code, int) and HTTPStatus.BAD_REQUEST <= status_code < HTTPStatus.INTERNAL_SERVER_ERROR

    async def _retry_async(self, fn: Callable[..., T], method_name: str, *args: object, **kwargs: object) -> T:
        """Retry a synchronous function on OSError / TimeoutError / XMLSyntaxError in the async layer."""
        total_attempts = 1 + self._config.retry_attempts
        last_exception: Exception | None = None

        for attempt in range(1, total_attempts + 1):
            try:
                logger.debug(
                    "Executing CSW retry helper method %s attempt %d/%d",
                    method_name,
                    attempt,
                    total_attempts,
                )
                return await self._run_in_executor(fn, *args, **kwargs)
            except CswConnectionError as exc:
                cause = exc.__cause__
                if isinstance(cause, (OSError, TimeoutError)) and not self._is_http_client_error(cause):
                    last_exception = exc
                else:
                    logger.debug(
                        "Non-retryable CSW error in %s: %s",
                        method_name,
                        exc,
                        exc_info=True,
                    )
                    raise
            except (OSError, TimeoutError) as exc:
                if self._is_http_client_error(exc):
                    logger.debug(
                        "Non-retryable HTTP client error in %s: %s",
                        method_name,
                        exc,
                        exc_info=True,
                    )
                    raise
                last_exception = exc
            except lxml.etree.XMLSyntaxError as exc:
                # The CSW endpoint returned an HTML error page instead of XML (transient server error)
                last_exception = exc

            if attempt == total_attempts:
                logger.error(
                    "CSW retry helper reached final attempt %d/%d for %s and failed: %s",
                    attempt,
                    total_attempts,
                    method_name,
                    last_exception,
                )
                raise last_exception or RuntimeError("Retry helper exited without exception")

            logger.warning(
                "Retrying %s attempt %d/%d after transient error: %s",
                method_name,
                attempt,
                total_attempts,
                last_exception,
            )
            delay = self._config.retry_backoff_base * (self._config.retry_backoff_factor ** (attempt - 1))
            delay = min(delay * random.uniform(0.9, 1.1), self._config.retry_max_delay)
            logger.debug(
                "Waiting %.3fs before retrying %s",
                delay,
                method_name,
            )
            await asyncio.sleep(delay)

        raise last_exception or RuntimeError("Retry helper exited without exception")

    def _parse_iso_record(self, iso: MD_Metadata, record_uuid: str) -> InspireRecord:
        """Parse an OWSLib MD_Metadata object into an InspireRecord."""
        return self._parser.parse_record(iso, record_uuid)
