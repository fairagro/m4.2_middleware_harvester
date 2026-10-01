"""Remote JSON-LD context fetch with process-lifetime caching."""

from __future__ import annotations

from typing import cast
from urllib.parse import urlparse

from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.errors import ParserError
from middleware.shared.json_types import JsonObject, JsonValue

# Process-lifetime cache: URL → parsed JSON document (root or import target).
_DOCUMENT_CACHE: dict[str, JsonValue] = {}


def clear_context_document_cache() -> None:
    """Clear the process-lifetime context cache (for tests)."""
    _DOCUMENT_CACHE.clear()


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


async def _fetch_document(url: str, client: NiceHttpClient) -> JsonValue:
    try:
        response = await client.get_with_policy(
            url,
            follow_redirects=True,
            headers={"Accept": "application/ld+json, application/json"},
        )
        response.raise_for_status()
        return cast(JsonValue, response.json())
    except ParserError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ParserError(f"Failed to fetch JSON-LD context {url}: {exc}") from exc


async def ensure_document_cached(url: str, client: NiceHttpClient) -> JsonValue:
    """Return the cached JSON document for ``url``, fetching once on miss."""
    cached = _DOCUMENT_CACHE.get(url)
    if cached is not None:
        return cached
    document = await _fetch_document(url, client)
    _DOCUMENT_CACHE[url] = document
    return document


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


async def materialize_payload_contexts(
    payload: JsonObject,
    *,
    allowed_context_url: str | None,
    client: NiceHttpClient | None,
) -> JsonObject:
    """Return a copy of ``payload`` with remote contexts fully inlined.

    When ``allowed_context_url`` is set, only that exact IRI is accepted. When unset,
    absolute http(s) remote IRIs are still fetched (``ParserConfig`` warns at load).
    ``client`` is required whenever a remote context must be resolved.
    """
    assert_payload_remote_contexts_allowed(payload, allowed_context_url)
    remote_urls = remote_context_urls_in_value(payload)
    if not remote_urls or "@context" not in payload:
        return payload
    if client is None:
        raise ParserError("HTTP client is required to resolve remote JSON-LD @context")

    inlined = await _inline_context_value(payload["@context"], client, set())
    return {**payload, "@context": inlined}
