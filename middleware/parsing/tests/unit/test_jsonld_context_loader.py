"""Unit tests for the shared JSON-LD context loader / cache."""

from __future__ import annotations

import httpx
import pytest

from middleware.harvester.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.parsing.errors import ParserError
from middleware.parsing.jsonld_context_loader import (
    clear_context_document_cache,
    ensure_document_cached,
    materialize_payload_contexts,
)
from middleware.shared.json_types import JsonObject, JsonValue


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_context_document_cache()


def _transport(documents: dict[str, JsonValue]) -> httpx.MockTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="", headers={"content-type": "text/plain"})
        url = str(request.url)
        if url not in documents:
            return httpx.Response(404, text="missing")
        return httpx.Response(200, json=documents[url], headers={"content-type": "application/ld+json"})

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_ensure_document_cached_fetches_once() -> None:
    root = "https://ctx.example/root.json"
    hits = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        hits["n"] += 1
        return httpx.Response(200, json={"@context": {"@vocab": "http://schema.org/"}})

    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        first = await ensure_document_cached(root, client)
        second = await ensure_document_cached(root, client)

    assert first == second
    assert hits["n"] == 1


@pytest.mark.asyncio
async def test_materialize_inlines_root_and_import_and_caches_both() -> None:
    root = "https://ctx.example/root.json"
    imported = "https://ctx.example/import.json"
    documents = {
        root: {"@context": {"@import": imported, "title": "http://purl.org/dc/terms/title"}},
        imported: {"@context": {"@vocab": "http://example.org/vocab/"}},
    }
    hits: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        url = str(request.url)
        hits.append(url)
        return httpx.Response(200, json=documents[url])

    payload: JsonObject = {
        "@context": root,
        "@id": "https://example.org/1",
        "title": "One",
    }

    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        first = await materialize_payload_contexts(payload, allowed_context_url=root, client=client)
        second = await materialize_payload_contexts(payload, allowed_context_url=root, client=client)

    assert first["@context"] == {"@vocab": "http://example.org/vocab/", "title": "http://purl.org/dc/terms/title"}
    assert second["@context"] == first["@context"]
    assert hits.count(root) == 1
    assert hits.count(imported) == 1


@pytest.mark.asyncio
async def test_materialize_rejects_wrong_url_without_fetch() -> None:
    hits = {"n": 0}

    async def handler(_request: httpx.Request) -> httpx.Response:
        hits["n"] += 1
        return httpx.Response(200, json={})

    payload: JsonObject = {"@context": "https://evil.example/ctx", "@id": "https://example.org/1"}
    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(ParserError, match="Remote JSON-LD @context"):
            await materialize_payload_contexts(
                payload,
                allowed_context_url="https://ctx.example/root.json",
                client=client,
            )
    assert hits["n"] == 0


@pytest.mark.asyncio
async def test_materialize_requires_client_when_remote_present() -> None:
    payload: JsonObject = {"@context": "https://ctx.example/root.json", "@id": "https://example.org/1"}
    with pytest.raises(ParserError, match="HTTP client is required"):
        await materialize_payload_contexts(
            payload,
            allowed_context_url="https://ctx.example/root.json",
            client=None,
        )
    with pytest.raises(ParserError, match="HTTP client is required"):
        await materialize_payload_contexts(payload, allowed_context_url=None, client=None)


@pytest.mark.asyncio
async def test_materialize_fetches_when_unset() -> None:
    root = "https://ctx.example/root.json"
    documents = {root: {"@context": {"@vocab": "http://schema.org/"}}}
    hits = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        hits["n"] += 1
        return httpx.Response(200, json=documents[str(request.url)])

    payload: JsonObject = {"@context": root, "@id": "https://example.org/1"}
    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        first = await materialize_payload_contexts(payload, allowed_context_url=None, client=client)
        second = await materialize_payload_contexts(payload, allowed_context_url=None, client=client)

    assert first["@context"] == {"@vocab": "http://schema.org/"}
    assert second["@context"] == first["@context"]
    assert hits["n"] == 1
