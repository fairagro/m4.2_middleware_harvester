"""MyCoRe Solr Protocol implementation for discovery."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import ConfigDict, Field

from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.protocol import Protocol, ProtocolType, ProtocolTypeConfig
from middleware.harvester.errors import RecordProcessingError
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.shared.json_types import JsonValue

# Overridable defaults when absent from ``entry_url``. Operator-supplied
# query parameters always win for these. ``q=*:*`` matches Solr's usual
# match-all; narrow with an explicit ``q`` / ``fq`` on the URL when needed.
_DEFAULT_SOLR_PARAMS: tuple[tuple[str, str], ...] = (
    ("core", "main"),
    ("q", "*:*"),
    ("fl", "id"),
)

# Owned by the harvester: never taken from ``entry_url``.
_SOFTWARE_SOLR_PARAMS: tuple[tuple[str, str], ...] = (("wt", "json"),)
_SOFTWARE_OWNED_QUERY_NAMES = frozenset({"start", "wt"})


class MycoreSolrProtocolConfig(ProtocolTypeConfig):
    """Type-specific config for the MyCoRe Solr Protocol."""

    model_config = ConfigDict(populate_by_name=True)

    entry_url: Annotated[
        str,
        Field(
            description=(
                "MyCoRe Solr select entry-point URL. May be query-free; overridable "
                "query parameters merge with software-owned wt/start."
            ),
        ),
    ]
    page_size: Annotated[
        int,
        Field(
            description="Default Solr rows when entry_url has no rows parameter.",
            ge=1,
        ),
    ] = 200


@Protocol.register(ProtocolType.mycore_solr)
class MycoreSolrProtocol(Protocol):
    """Protocol for MyCoRe Solr-based discovery endpoints."""

    config: MycoreSolrProtocolConfig

    def __init__(self, config: MycoreSolrProtocolConfig, client: NiceHttpClient) -> None:
        """Initialize the MyCoRe Solr protocol and its page cache."""
        super().__init__(config, client)
        self._page_size = config.page_size
        self._first_page_cache: tuple[int, list[JsonValue], int] | None = None

    @property
    def _entry_url(self) -> str:
        return self.config.entry_url

    async def get_expected_count(self) -> int | None:
        """Return the total number of matching results, if the backend exposes it."""
        if self._first_page_cache is not None:
            return self._first_page_cache[0]

        num_found, docs, returned_start = await self._fetch_page(self._entry_url, self._client, 0)
        self._first_page_cache = (num_found, docs, returned_start)
        return num_found

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        base_url = self._build_base_url(self._entry_url)
        start = 0

        while True:
            if self._first_page_cache is not None and start == 0:
                num_found, docs, _returned_start = self._first_page_cache
                self._first_page_cache = None
            else:
                num_found, docs, _returned_start = await self._fetch_page(self._entry_url, client, start)
            if not docs:
                break

            for index, doc in enumerate(docs):
                synthetic_id = f"mycore_solr:start={start}:index={index}"
                if not isinstance(doc, dict):
                    yield RecordProcessingError(
                        (f"MyCoRe Solr doc at start={start} index={index} is not an object (got {type(doc).__name__})"),
                        synthetic_id,
                    )
                    continue

                object_id = doc.get("id")
                if not isinstance(object_id, str) or not object_id.strip():
                    yield RecordProcessingError(
                        f"MyCoRe Solr doc at start={start} index={index} is missing id",
                        synthetic_id,
                    )
                    continue

                yield UrlDiscoveryResult(
                    f"{base_url}/receive/{object_id.strip()}",
                    harvest_source_id=object_id.strip(),
                )

            start += len(docs)
            if start >= num_found:
                break

    async def _fetch_page(
        self,
        entry_url: str,
        client: NiceHttpClient,
        start: int,
    ) -> tuple[int, list[JsonValue], int]:
        request_url = self._build_request_url(entry_url, start, self._page_size)
        response = await client.get_with_policy(request_url)

        payload = response.json()
        if not isinstance(payload, dict):
            raise GenericProtocolError(f"Solr response must be a JSON object (got {type(payload).__name__})")
        response_object = payload.get("response")
        if not isinstance(response_object, dict):
            raise GenericProtocolError("Missing Solr response envelope: response")

        num_found = response_object.get("numFound")
        if not isinstance(num_found, int):
            raise GenericProtocolError("Missing or invalid response.numFound")

        returned_start = response_object.get("start")
        if not isinstance(returned_start, int):
            raise GenericProtocolError("Missing or invalid response.start")

        docs = response_object.get("docs")
        if not isinstance(docs, list):
            raise GenericProtocolError("Missing expected response.docs array")

        return num_found, docs, returned_start

    @staticmethod
    def _build_request_url(entry_url: str, start: int, page_size: int) -> str:
        """Build a Solr request URL with defaults and operator overrides.

        ``entry_url`` may be a query-free select endpoint
        (e.g. ``https://host/servlets/solr/select``). Missing overridable
        parameters (``core``, ``q``, ``fl``, ``rows``) are filled
        automatically; operator-supplied values for those keys win.
        ``wt=json`` and pagination ``start`` are always set by the software
        (values from ``entry_url`` are ignored) because the parser requires
        the Solr JSON response envelope.
        """
        parsed_url = urlparse(entry_url)
        operator_pairs = [
            (name, value)
            for name, value in parse_qsl(parsed_url.query, keep_blank_values=True)
            if name not in _SOFTWARE_OWNED_QUERY_NAMES
        ]
        operator_names = {name for name, _ in operator_pairs}

        query_pairs: list[tuple[str, str]] = [
            (name, value) for name, value in _DEFAULT_SOLR_PARAMS if name not in operator_names
        ]
        if "rows" not in operator_names:
            query_pairs.append(("rows", str(page_size)))
        query_pairs.extend(operator_pairs)
        query_pairs.extend(_SOFTWARE_SOLR_PARAMS)
        query_pairs.append(("start", str(start)))
        return urlunparse(parsed_url._replace(query=urlencode(query_pairs), params="", fragment=""))

    @staticmethod
    def _build_base_url(entry_url: str) -> str:
        parsed_url = urlparse(entry_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid entry URL: {entry_url}")
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
