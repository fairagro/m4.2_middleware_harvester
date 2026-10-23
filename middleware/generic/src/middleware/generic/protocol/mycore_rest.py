"""MyCoRe REST Protocol — list ``api/v2/objects`` and yield REST object URLs."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
import lxml.etree  # type: ignore[import-untyped]
from pydantic import ConfigDict, Field

from middleware.contracts.errors import RecordProcessingError
from middleware.contracts.nice_http_client import NiceHttpClient
from middleware.generic.errors import GenericProtocolError
from middleware.generic.protocol.protocol import Protocol, ProtocolType, ProtocolTypeConfig
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.parsing.xml_hardening import HARDENED_XML_PARSER

# Owned by the harvester: never taken from ``entry_url``.
_SOFTWARE_OWNED_QUERY_NAMES = frozenset({"after_id", "limit", "offset"})


class MycoreRestProtocolConfig(ProtocolTypeConfig):
    """Type-specific config for the MyCoRe REST Protocol."""

    model_config = ConfigDict(populate_by_name=True)

    entry_url: Annotated[
        str,
        Field(
            description=(
                "MyCoRe REST objects list URL (e.g. ``…/api/v2/objects?category=…``). "
                "Operator filters are forwarded; ``limit`` / ``after_id`` are software-owned."
            ),
        ),
    ]
    page_size: Annotated[
        int,
        Field(
            description="Page size written as the ``limit`` query parameter.",
            ge=1,
        ),
    ] = 200


@Protocol.register(ProtocolType.mycore_rest)
class MycoreRestProtocol(Protocol):
    """Protocol for MyCoRe REST ``api/v2/objects`` discovery."""

    config: MycoreRestProtocolConfig

    def __init__(self, config: MycoreRestProtocolConfig, client: NiceHttpClient) -> None:
        """Initialize the MyCoRe REST protocol and first-page cache."""
        super().__init__(config, client)
        self._page_size = config.page_size
        self._first_page_cache: tuple[int | None, list[str], str | None] | None = None

    @property
    def _entry_url(self) -> str:
        return self.config.entry_url

    async def get_expected_count(self) -> int | None:
        """Return ``X-Total-Count`` from the first list page when present."""
        if self._first_page_cache is not None:
            return self._first_page_cache[0]

        total, ids, _last_id = await self._fetch_page(self._entry_url, self._client, after_id=None)
        self._first_page_cache = (total, ids, ids[-1] if ids else None)
        return total

    async def _discover(self, client: NiceHttpClient) -> AsyncGenerator[DiscoveryResult | RecordProcessingError, None]:
        objects_base = self._objects_collection_url(self._entry_url)
        after_id: str | None = None

        while True:
            if self._first_page_cache is not None and after_id is None:
                _total, ids, last_id = self._first_page_cache
                self._first_page_cache = None
            else:
                _total, ids, last_id = await self._fetch_page(self._entry_url, client, after_id=after_id)

            if not ids:
                break

            for index, object_id in enumerate(ids):
                if not object_id.strip():
                    yield RecordProcessingError(
                        f"MyCoRe REST list entry at after_id={after_id!r} index={index} has empty id",
                        f"mycore_rest:after_id={after_id}:index={index}",
                    )
                    continue
                stripped = object_id.strip()
                yield UrlDiscoveryResult(
                    f"{objects_base}/{stripped}",
                    harvest_source_id=stripped,
                )

            if len(ids) < self._page_size or last_id is None:
                break
            after_id = last_id

    async def _fetch_page(
        self,
        entry_url: str,
        client: NiceHttpClient,
        *,
        after_id: str | None,
    ) -> tuple[int | None, list[str], str | None]:
        request_url = self._build_request_url(entry_url, after_id=after_id, page_size=self._page_size)
        try:
            response = await client.get_with_policy(request_url)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            raise GenericProtocolError(f"MyCoRe REST list failed HTTP {status} for {request_url}") from exc
        if response.is_error:
            raise GenericProtocolError(f"MyCoRe REST list failed HTTP {response.status_code} for {request_url}")

        total = self._parse_total_count(response.headers.get("X-Total-Count"))
        try:
            root = lxml.etree.fromstring(response.content, parser=HARDENED_XML_PARSER)
        except lxml.etree.XMLSyntaxError as exc:
            raise GenericProtocolError(f"MyCoRe REST list is not well-formed XML: {exc}") from exc

        ids = self._object_ids_from_list(root)
        last_id = ids[-1] if ids else None
        return total, ids, last_id

    @staticmethod
    def _parse_total_count(raw: str | None) -> int | None:
        if raw is None:
            return None
        try:
            value = int(raw.strip())
        except ValueError:
            return None
        return value if value >= 0 else None

    @staticmethod
    def _object_ids_from_list(root: lxml.etree._Element) -> list[str]:
        local = lxml.etree.QName(root).localname if root.tag is not None else ""
        if local not in {"mycoreobjects", "mycoreobject"}:
            # Tolerate a document element that still contains mycoreobject children.
            pass
        ids: list[str] = []
        for node in root.iter():
            if lxml.etree.QName(node).localname != "mycoreobject":
                continue
            object_id = node.get("id")
            if object_id is not None:
                ids.append(object_id)
        return ids

    @staticmethod
    def _build_request_url(entry_url: str, *, after_id: str | None, page_size: int) -> str:
        parsed_url = urlparse(entry_url)
        operator_pairs = [
            (name, value)
            for name, value in parse_qsl(parsed_url.query, keep_blank_values=True)
            if name not in _SOFTWARE_OWNED_QUERY_NAMES
        ]
        query_pairs: list[tuple[str, str]] = [*operator_pairs, ("limit", str(page_size))]
        if after_id is not None:
            query_pairs.append(("after_id", after_id))
        return urlunparse(parsed_url._replace(query=urlencode(query_pairs), params="", fragment=""))

    @staticmethod
    def _objects_collection_url(entry_url: str) -> str:
        """Return the ``…/api/v2/objects`` collection URL (no query, no object id / list file).

        Live OpenAgrar uses ``…/api/v2/objects?…``. Fixture trees may use a list file under
        ``…/api/v2/objects/list.xml``; truncate to the ``/objects`` segment in that case.
        """
        parsed_url = urlparse(entry_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid entry URL: {entry_url}")
        path = parsed_url.path.rstrip("/")
        marker = "/objects"
        collection_path = path[: path.index(marker) + len(marker)] if marker in path else path
        return urlunparse((parsed_url.scheme, parsed_url.netloc, collection_path, "", "", ""))
