"""Remote JSON-LD context fetch with process-lifetime caching."""

from __future__ import annotations

import asyncio
from typing import cast
from urllib.parse import urljoin, urlparse

import httpx

from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.errors import ParserError
from middleware.shared.json_types import JsonObject, JsonValue

# Process-lifetime cache: URL → parsed JSON document (root or import target).
_DOCUMENT_CACHE: dict[str, JsonValue] = {}
# In-flight fetch tasks so concurrent misses share one GET per URL.
_INFLIGHT: dict[str, asyncio.Task[JsonValue]] = {}
_CACHE_LOCK = asyncio.Lock()

_JSON_DOCUMENT_TYPES = frozenset({"application/ld+json", "application/json"})


def clear_context_document_cache() -> None:
    """Clear the process-lifetime context cache (for tests)."""
    _DOCUMENT_CACHE.clear()
    _INFLIGHT.clear()


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


def assert_payload_remote_contexts_allowed(payload: JsonObject, allowed_context_url: str | None) -> None:
    """Validate remote context IRIs in ``payload``.

    Absolute http(s) IRIs are always required. When ``allowed_context_url`` is set, every
    remote IRI MUST equal that URL. When unset, any absolute http(s) IRI is accepted
    (``ParserConfig`` warns at load time; fetch still uses the shared cache).
    """
    for url in remote_context_urls_in_value(payload):
        if not _is_absolute_http_url(url):
            raise ParserError(f"Relative or non-http(s) JSON-LD context reference is not supported: {url!r}")
        if allowed_context_url is not None and url != allowed_context_url:
            raise ParserError(f"Remote JSON-LD @context is not supported: {url!r}")


def _content_type_base(response: httpx.Response) -> str:
    raw = response.headers.get("content-type", "")
    return str(raw).split(";")[0].strip().lower()


def _is_json_document_type(content_type: str) -> bool:
    return content_type in _JSON_DOCUMENT_TYPES or content_type.endswith("+json")


def _jsonld_alternate_url(response: httpx.Response, base_url: str) -> str | None:
    """Return a ``rel=alternate`` JSON-LD URL from ``Link``, if present (JSON-LD 1.1 §9.4.1)."""
    link = response.links.get("alternate")
    if not link:
        return None
    link_type = str(link.get("type", "")).split(";")[0].strip().lower()
    if link_type and link_type not in _JSON_DOCUMENT_TYPES:
        return None
    href = link.get("url")
    if not href:
        return None
    return urljoin(base_url, href)


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


async def _fetch_and_store(url: str, client: NiceHttpClient) -> JsonValue:
    document = await _fetch_document(url, client)
    _DOCUMENT_CACHE[url] = document
    return document


async def ensure_document_cached(url: str, client: NiceHttpClient) -> JsonValue:
    """Return the cached JSON document for ``url``, fetching once on miss.

    Concurrent callers share a single in-flight fetch task per URL. Awaiters use
    ``asyncio.shield`` so cancelling one waiter does not cancel the shared fetch.
    """
    cached = _DOCUMENT_CACHE.get(url)
    if cached is not None:
        return cached
    async with _CACHE_LOCK:
        cached = _DOCUMENT_CACHE.get(url)
        if cached is not None:
            return cached
        task = _INFLIGHT.get(url)
        if task is None:
            task = asyncio.create_task(_fetch_and_store(url, client))
            _INFLIGHT[url] = task
    try:
        return await asyncio.shield(task)
    finally:
        async with _CACHE_LOCK:
            if _INFLIGHT.get(url) is task:
                _INFLIGHT.pop(url, None)


def _unwrap_context_document(document: JsonValue) -> JsonValue:
    """Return the JSON-LD context value from a remote document envelope when present."""
    if isinstance(document, dict) and "@context" in document:
        keys = set(document.keys())
        if keys == {"@context"} or keys <= {"@context", "@graph", "@id", "@type"}:
            return document["@context"]
    return document


async def _inline_remote_string(url: str, client: NiceHttpClient, stack: set[str]) -> JsonValue:
    if not _is_absolute_http_url(url):
        raise ParserError(f"Relative or non-http(s) JSON-LD context reference is not supported: {url!r}")
    if url in stack:
        raise ParserError(f"Recursive JSON-LD context inclusion: {url}")
    stack.add(url)
    try:
        document = await ensure_document_cached(url, client)
        return await _inline_context_value(_unwrap_context_document(document), client, stack)
    finally:
        stack.discard(url)


async def _apply_import(context_obj: JsonObject, client: NiceHttpClient, stack: set[str]) -> JsonObject:
    import_url = context_obj.get("@import")
    if import_url is None:
        return context_obj
    if not isinstance(import_url, str):
        raise ParserError("JSON-LD @import must be a string URL")
    imported = await _inline_remote_string(import_url, client, stack)
    if not isinstance(imported, dict):
        raise ParserError(f"JSON-LD @import target must resolve to an object context: {import_url}")
    merged: JsonObject = dict(imported)
    for key, item in context_obj.items():
        if key != "@import":
            merged[key] = item
    return merged


async def _inline_context_value(value: JsonValue, client: NiceHttpClient, stack: set[str]) -> JsonValue:
    """Return ``value`` with remote string / ``@import`` references fully inlined."""
    if isinstance(value, str):
        return await _inline_remote_string(value, client, stack)
    if isinstance(value, list):
        return [await _inline_context_value(item, client, stack) for item in value]
    if isinstance(value, dict):
        working = await _apply_import(value, client, stack)
        out: JsonObject = {}
        for key, item in working.items():
            # Only ``@context`` nests further remote docs; ``@vocab`` / term IRIs stay literal.
            out[key] = await _inline_context_value(item, client, stack) if key == "@context" else item
        return out
    return value


async def _inline_document_remotes(node: JsonValue, client: NiceHttpClient, stack: set[str]) -> JsonValue:
    """Inline every remote ``@context`` / ``@import`` reachable in ``node``."""
    if isinstance(node, list):
        return [await _inline_document_remotes(item, client, stack) for item in node]
    if not isinstance(node, dict):
        return node
    working = await _apply_import(node, client, stack) if "@import" in node else node
    out: JsonObject = {}
    for key, item in working.items():
        if key == "@context":
            out[key] = await _inline_context_value(item, client, stack)
        else:
            out[key] = await _inline_document_remotes(item, client, stack)
    return out


async def materialize_payload_contexts(
    payload: JsonObject,
    *,
    allowed_context_url: str | None,
    client: NiceHttpClient | None,
) -> JsonObject:
    """Return ``payload`` with remote contexts fully inlined when needed.

    When there is nothing to resolve, returns ``payload`` unchanged. Otherwise returns a
    deep-walked copy with every remote ``@context`` / ``@import`` inlined through the
    shared cache (not only a top-level ``@context``).

    When ``allowed_context_url`` is set, only that exact IRI is accepted. When unset,
    absolute http(s) remote IRIs are still fetched (``ParserConfig`` warns at load).
    ``client`` is required whenever a remote context must be resolved.
    """
    assert_payload_remote_contexts_allowed(payload, allowed_context_url)
    remote_urls = remote_context_urls_in_value(payload)
    if not remote_urls:
        return payload
    if client is None:
        raise ParserError("HTTP client is required to resolve remote JSON-LD @context")

    inlined = await _inline_document_remotes(payload, client, set())
    if not isinstance(inlined, dict):
        raise ParserError("JSON-LD payload must be a JSON object after context materialization")
    return inlined
