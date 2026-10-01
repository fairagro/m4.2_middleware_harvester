"""Regal ``/find`` Protocol implementation (offset-paginated JSON array).

Pages through a Regal ``/find`` endpoint (``format=json``) whose response is a
JSON array of inline Regal JSON-LD records and yields one inline
``JsonLdDiscoveryResult`` per record, keyed by the record's ``@id``.

Array handling is shared with other JSON array sources (``JsonArrayProtocol``);
this Protocol only adds ``from``/``until`` pagination, the ``/find`` query
contract, and ``@id`` identity. The endpoint URL is ``config.entry_url``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import ConfigDict, Field

from middleware.generic.protocol.json_array import JsonArrayProtocol
from middleware.generic.protocol.protocol import Protocol, ProtocolType, ProtocolTypeConfig
from middleware.harvester.nice_http_client import NiceHttpClient

# Overridable defaults when absent from ``entry_url``. Operator-supplied
# query parameters always win for these (and any other non-owned keys).
_DEFAULT_REGAL_PARAMS: tuple[tuple[str, str], ...] = (("q", "contentType:researchData"),)

# Owned by the harvester: never taken from ``entry_url``.
# ``until`` is resolved once (URL override or config ``page_size``) and always
# written by the software so pagination stop conditions stay consistent.
_SOFTWARE_REGAL_PARAMS: tuple[tuple[str, str], ...] = (("format", "json"),)
_SOFTWARE_OWNED_QUERY_NAMES = frozenset({"from", "format", "until"})


class RegalFindProtocolConfig(ProtocolTypeConfig):
    """Type-specific config for the Regal ``/find`` Protocol."""

    model_config = ConfigDict(populate_by_name=True)

    entry_url: Annotated[
        str,
        Field(
            description=(
                "Regal /find entry-point URL. May be query-free; overridable query "
                "parameters merge with software-owned format/from/until."
            ),
        ),
    ]
    page_size: Annotated[
        int,
        Field(
            description="Default /find until when entry_url has no until parameter.",
            ge=1,
        ),
    ] = 200


@Protocol.register(ProtocolType.regal_find)
class RegalFindProtocol(JsonArrayProtocol):
    """Protocol for Regal ``/find`` JSON endpoints with inline metadata."""

    config: RegalFindProtocolConfig
    record_id_prefix = "regal_find"
    source_label = "Regal /find"

    def __init__(self, config: RegalFindProtocolConfig, client: NiceHttpClient) -> None:
        """Initialize and resolve the page size (URL ``until`` or config ``page_size``)."""
        super().__init__(config, client)
        self._page_size = self._resolve_page_size(config.entry_url, config.page_size)

    async def get_expected_count(self) -> int | None:  # noqa: PLR6301
        """Return None; Regal ``/find`` does not expose a total hit count."""
        return None

    async def _pages(self, client: NiceHttpClient) -> AsyncGenerator[tuple[tuple[str, ...], list[object]], None]:
        offset = 0
        while True:
            request_url = self._build_request_url(self.config.entry_url, offset, self._page_size)
            page = await self._fetch_array(request_url, client)
            if not page:
                return
            yield (f"from={offset}",), page
            if len(page) < self._page_size:
                return
            offset += len(page)

    def _record_identifier(self, record: dict[str, object]) -> str | None:  # noqa: PLR6301
        """Return the Regal ``@id``; DOI is not used as a discovery identity."""
        record_id = record.get("@id")
        if isinstance(record_id, str) and record_id.strip():
            return record_id.strip()
        return None

    @staticmethod
    def _resolve_page_size(entry_url: str, page_size: int) -> int:
        """Return URL ``until`` when present and valid; otherwise config ``page_size``."""
        for name, value in parse_qsl(urlparse(entry_url).query, keep_blank_values=True):
            if name != "until":
                continue
            try:
                parsed = int(value)
            except ValueError:
                break
            if parsed >= 1:
                return parsed
            break
        return page_size

    @staticmethod
    def _build_request_url(entry_url: str, offset: int, page_size: int) -> str:
        """Build a ``/find`` request URL with defaults and operator overrides.

        ``entry_url`` may be a query-free ``/find`` endpoint. Missing
        overridable parameters (notably ``q``) are filled from defaults.
        Operator-supplied values for those keys win; extra filter/sort params
        are forwarded. ``format=json``, pagination ``from``, and ``until``
        (resolved from URL ``until`` or config ``page_size``) are always set
        by the software because discovery parses a JSON array response.
        """
        parsed_url = urlparse(entry_url)
        operator_pairs = [
            (name, value)
            for name, value in parse_qsl(parsed_url.query, keep_blank_values=True)
            if name not in _SOFTWARE_OWNED_QUERY_NAMES
        ]
        operator_names = {name for name, _ in operator_pairs}

        query_pairs: list[tuple[str, str]] = [
            (name, value) for name, value in _DEFAULT_REGAL_PARAMS if name not in operator_names
        ]
        query_pairs.extend(operator_pairs)
        query_pairs.extend(_SOFTWARE_REGAL_PARAMS)
        query_pairs.append(("until", str(page_size)))
        query_pairs.append(("from", str(offset)))
        return urlunparse(parsed_url._replace(query=urlencode(query_pairs), params="", fragment=""))
