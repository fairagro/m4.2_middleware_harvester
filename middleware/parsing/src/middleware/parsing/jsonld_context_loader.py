"""Remote JSON-LD context fetch with process-lifetime caching."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from typing import cast
from urllib.parse import urljoin, urlparse

import httpx

from middleware.contracts.nice_http_client import NiceHttpClient
from middleware.parsing.allowed_context import context_url_is_allowed, validate_allowed_context_url_value
from middleware.parsing.errors import ParserError
from middleware.shared.json_types import JsonObject, JsonValue

_JSON_DOCUMENT_TYPES = frozenset({"application/ld+json", "application/json"})


def _is_absolute_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _collect_remote_strings(node: JsonValue, found: list[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_remote_strings(item, found)
        return
    if not isinstance(node, dict):
        return
    for key, item in node.items():
        if key in {"@context", "@import"}:
            _collect_context_key_strings(item, found)
        else:
            _collect_remote_strings(item, found)


def _collect_context_key_strings(item: JsonValue, found: list[str]) -> None:
    if isinstance(item, str):
        found.append(item)
        return
    if isinstance(item, list):
        for entry in item:
            if isinstance(entry, str):
                found.append(entry)
            else:
                _collect_remote_strings(entry, found)
        return
    _collect_remote_strings(item, found)


def remote_context_urls_in_value(value: JsonValue) -> list[str]:
    """Collect remote ``@context`` / ``@import`` string IRIs reachable from ``value``."""
    found: list[str] = []
    _collect_remote_strings(value, found)
    return found


def assert_payload_remote_contexts_allowed(
    payload: JsonObject,
    allowed_context_url: str | list[str] | None,
) -> None:
    """Validate remote context IRIs in ``payload``.

    Absolute http(s) IRIs are always required. When ``allowed_context_url`` is set (one
    IRI or a list), every remote IRI MUST match an entry after trailing-slash
    normalisation; an ``http`` allowlist entry also matches the same IRI under
    ``https``. Inline object contexts in a ``@context`` list remain allowed.
    When unset, any absolute http(s) IRI is accepted (``ParserConfig`` warns at load;
    fetch still uses the shared cache).
    """
    allowed = validate_allowed_context_url_value(allowed_context_url)
    for url in remote_context_urls_in_value(payload):
        if not _is_absolute_http_url(url):
            raise ParserError(f"Relative or non-http(s) JSON-LD context reference is not supported: {url!r}")
        if not context_url_is_allowed(url, allowed):
            raise ParserError(f"Remote JSON-LD @context is not supported: {url!r}")


def _content_type_base(response: httpx.Response) -> str:
    raw = response.headers.get("content-type", "")
    return str(raw).split(";", maxsplit=1)[0].strip().lower()


def _is_json_document_type(content_type: str) -> bool:
    return content_type in _JSON_DOCUMENT_TYPES or content_type.endswith("+json")


def _jsonld_alternate_url(response: httpx.Response, base_url: str) -> str | None:
    """Return a ``rel=alternate`` JSON-LD URL from ``Link``, if present (JSON-LD 1.1 §9.4.1)."""
    link = response.links.get("alternate")
    if not link:
        return None
    link_type = str(link.get("type", "")).split(";", maxsplit=1)[0].strip().lower()
    if link_type and link_type not in _JSON_DOCUMENT_TYPES:
        return None
    href = link.get("url")
    if not href:
        return None
    return urljoin(base_url, href)


def _unwrap_context_document(document: JsonValue) -> JsonValue:
    """Return the JSON-LD context value from a remote document envelope when present.

    Context documents MAY carry additional metadata keys beside ``@context``; when
    the document is referenced as a remote ``@context`` / ``@import`` target, only
    the ``@context`` member is inlined.
    """
    if isinstance(document, dict) and "@context" in document:
        return document["@context"]
    return document


async def _get_context_response(url: str, client: NiceHttpClient) -> httpx.Response:
    response = await client.get_with_policy(
        url,
        follow_redirects=True,
        headers={"Accept": "application/ld+json, application/json"},
    )
    response.raise_for_status()
    return response


async def _parse_json_response(url: str, response: httpx.Response) -> JsonValue:
    try:
        return cast(JsonValue, response.json())
    except Exception as exc:  # noqa: BLE001
        raise ParserError(f"Failed to parse JSON-LD context {url}: {exc}") from exc


async def _fetch_document(url: str, client: NiceHttpClient) -> JsonValue:
    try:
        response = await _get_context_response(url, client)
        if _is_json_document_type(_content_type_base(response)):
            return await _parse_json_response(url, response)
        alternate = _jsonld_alternate_url(response, str(response.url))
        if alternate is None:
            raise ParserError(
                f"JSON-LD context {url} did not return JSON "
                f"(content-type={_content_type_base(response)!r}) and has no "
                f"Link rel=alternate type=application/ld+json"
            )
        alt_response = await _get_context_response(alternate, client)
        if not _is_json_document_type(_content_type_base(alt_response)):
            raise ParserError(
                f"JSON-LD context alternate {alternate} for {url} did not return JSON "
                f"(content-type={_content_type_base(alt_response)!r})"
            )
        return await _parse_json_response(alternate, alt_response)
    except ParserError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ParserError(f"Failed to fetch JSON-LD context {url}: {exc}") from exc


class JsonLdContextLoader:
    """Fetch and inline remote JSON-LD contexts with a bounded process cache."""

    def __init__(self) -> None:
        """Create an empty loader with an uncapped document cache."""
        self._max_entries: int | None = None
        self._documents: OrderedDict[str, JsonValue] = OrderedDict()
        self._inflight: dict[str, asyncio.Task[JsonValue]] = {}
        self._lock = asyncio.Lock()

    @property
    def max_entries(self) -> int | None:
        """Configured cache size cap, or ``None`` if uncapped / not yet configured."""
        return self._max_entries

    def configure_max_entries(self, max_entries: int) -> None:
        """Set the document cache size cap. ``max_entries`` MUST be >= 1."""
        if max_entries < 1:
            raise ValueError("jsonld_context_cache_max_entries must be >= 1")
        self._max_entries = max_entries

    def clear(self) -> None:
        """Clear cached documents, in-flight tasks, and the size cap (for tests)."""
        self._documents.clear()
        self._inflight.clear()
        self._max_entries = None

    def _put(self, url: str, document: JsonValue) -> None:
        if url in self._documents:
            self._documents.move_to_end(url)
        self._documents[url] = document
        max_entries = self._max_entries
        if max_entries is None:
            return
        while len(self._documents) > max_entries:
            self._documents.popitem(last=False)

    async def _fetch_and_store(self, url: str, client: NiceHttpClient) -> JsonValue:
        document = await _fetch_document(url, client)
        async with self._lock:
            self._put(url, document)
        return document

    async def ensure_document_cached(self, url: str, client: NiceHttpClient) -> JsonValue:
        """Return the cached JSON document for ``url``, fetching once on miss.

        Concurrent callers share a single in-flight fetch task per URL. Awaiters use
        ``asyncio.shield`` so cancelling one waiter does not cancel the shared fetch.
        """
        async with self._lock:
            cached = self._documents.get(url)
            if cached is not None:
                self._documents.move_to_end(url)
                return cached
            task = self._inflight.get(url)
            if task is None:
                task = asyncio.create_task(self._fetch_and_store(url, client))
                self._inflight[url] = task
        try:
            return await asyncio.shield(task)
        finally:
            async with self._lock:
                if self._inflight.get(url) is task:
                    self._inflight.pop(url, None)

    async def _inline_remote_string(self, url: str, client: NiceHttpClient, stack: set[str]) -> JsonValue:
        if not _is_absolute_http_url(url):
            raise ParserError(f"Relative or non-http(s) JSON-LD context reference is not supported: {url!r}")
        if url in stack:
            raise ParserError(f"Recursive JSON-LD context inclusion: {url}")
        stack.add(url)
        try:
            # Module facade (patchable in tests) → process-lifetime singleton.
            document = await ensure_document_cached(url, client)
            return await self._inline_context_value(_unwrap_context_document(document), client, stack)
        finally:
            stack.discard(url)

    async def _apply_import(self, context_obj: JsonObject, client: NiceHttpClient, stack: set[str]) -> JsonObject:
        import_url = context_obj.get("@import")
        if import_url is None:
            return context_obj
        if not isinstance(import_url, str):
            raise ParserError("JSON-LD @import must be a string URL")
        imported = await self._inline_remote_string(import_url, client, stack)
        if not isinstance(imported, dict):
            raise ParserError(f"JSON-LD @import target must resolve to an object context: {import_url}")
        merged: JsonObject = dict(imported)
        for key, item in context_obj.items():
            if key != "@import":
                merged[key] = item
        return merged

    async def _inline_context_value(self, value: JsonValue, client: NiceHttpClient, stack: set[str]) -> JsonValue:
        """Return ``value`` with remote string / ``@import`` references fully inlined."""
        if isinstance(value, str):
            return await self._inline_remote_string(value, client, stack)
        if isinstance(value, list):
            return [await self._inline_context_value(item, client, stack) for item in value]
        if isinstance(value, dict):
            working = await self._apply_import(value, client, stack)
            out: JsonObject = {}
            for key, item in working.items():
                # Only ``@context`` nests further remote docs; ``@vocab`` / term IRIs stay literal.
                out[key] = await self._inline_context_value(item, client, stack) if key == "@context" else item
            return out
        return value

    async def _inline_document_remotes(self, node: JsonValue, client: NiceHttpClient, stack: set[str]) -> JsonValue:
        """Inline every remote ``@context`` / ``@import`` reachable in ``node``."""
        if isinstance(node, list):
            return [await self._inline_document_remotes(item, client, stack) for item in node]
        if not isinstance(node, dict):
            return node
        working = await self._apply_import(node, client, stack) if "@import" in node else node
        out: JsonObject = {}
        for key, item in working.items():
            if key == "@context":
                out[key] = await self._inline_context_value(item, client, stack)
            else:
                out[key] = await self._inline_document_remotes(item, client, stack)
        return out

    async def materialize_payload_contexts(
        self,
        payload: JsonObject,
        *,
        allowed_context_url: str | list[str] | None,
        client: NiceHttpClient | None,
    ) -> JsonObject:
        """Return ``payload`` with remote contexts fully inlined when needed.

        When there is nothing to resolve, returns ``payload`` unchanged. Otherwise returns a
        deep-walked copy with every remote ``@context`` / ``@import`` inlined through this
        loader's cache (not only a top-level ``@context``).

        When ``allowed_context_url`` is set (one IRI or a list), every remote IRI must match
        an entry after trailing-slash normalisation (``http`` entries also match ``https``).
        When unset, absolute http(s) remotes are still fetched (``ParserConfig`` warns at
        load). ``client`` is required whenever a remote context must be resolved.
        """
        assert_payload_remote_contexts_allowed(payload, allowed_context_url)
        remote_urls = remote_context_urls_in_value(payload)
        if not remote_urls:
            return payload
        if client is None:
            raise ParserError("HTTP client is required to resolve remote JSON-LD @context")

        inlined = await self._inline_document_remotes(payload, client, set())
        if not isinstance(inlined, dict):
            raise ParserError("JSON-LD payload must be a JSON object after context materialization")
        return inlined


# Process-lifetime singleton used by parsers; cap set at harvest startup.
_LOADER = JsonLdContextLoader()


def configure_document_cache_max_entries(max_entries: int) -> None:
    """Set the process-lifetime context-document cache size cap.

    Called once from the harvester entrypoint after loading
    ``Config.jsonld_context_cache_max_entries``. ``max_entries`` MUST be >= 1.
    """
    _LOADER.configure_max_entries(max_entries)


def document_cache_max_entries() -> int | None:
    """Return the configured cache size cap, or ``None`` if not yet configured."""
    return _LOADER.max_entries


def clear_context_document_cache() -> None:
    """Clear the process-lifetime context cache (for tests)."""
    _LOADER.clear()


async def ensure_document_cached(url: str, client: NiceHttpClient) -> JsonValue:
    """Return the cached JSON document for ``url`` via the process-lifetime loader."""
    return await _LOADER.ensure_document_cached(url, client)


async def materialize_payload_contexts(
    payload: JsonObject,
    *,
    allowed_context_url: str | list[str] | None,
    client: NiceHttpClient | None,
) -> JsonObject:
    """Return ``payload`` with remote contexts fully inlined via the process-lifetime loader."""
    return await _LOADER.materialize_payload_contexts(
        payload,
        allowed_context_url=allowed_context_url,
        client=client,
    )
