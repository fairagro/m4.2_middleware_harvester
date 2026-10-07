"""Unit tests for the shared JSON-LD context loader / cache."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from middleware.contracts.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.parsing.errors import ParserError
from middleware.parsing.jsonld_context_loader import (
    clear_context_document_cache,
    configure_document_cache_max_entries,
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
    accepts: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        hits["n"] += 1
        accepts.append(request.headers.get("accept", ""))
        return httpx.Response(200, json={"@context": {"@vocab": "http://schema.org/"}})

    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        first = await ensure_document_cached(root, client)
        second = await ensure_document_cached(root, client)

    assert first == second
    assert hits["n"] == 1
    assert accepts == ["application/ld+json, application/json"]


@pytest.mark.asyncio
async def test_ensure_document_cached_shares_inflight_fetch() -> None:
    root = "https://ctx.example/root.json"
    hits = {"n": 0}
    release = asyncio.Event()

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        hits["n"] += 1
        await release.wait()
        return httpx.Response(200, json={"@context": {"@vocab": "http://schema.org/"}})

    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        first_task = asyncio.create_task(ensure_document_cached(root, client))
        second_task = asyncio.create_task(ensure_document_cached(root, client))
        await asyncio.sleep(0.05)
        assert hits["n"] == 1
        release.set()
        first, second = await asyncio.gather(first_task, second_task)

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


@pytest.mark.asyncio
async def test_ensure_document_cached_follows_jsonld_link_alternate() -> None:
    root = "https://schema.org/"
    alternate = "https://schema.org/docs/jsonldcontext.jsonld"
    hits: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        url = str(request.url)
        hits.append(url)
        if url == root:
            return httpx.Response(
                200,
                text="<html></html>",
                headers={
                    "content-type": "text/html",
                    "link": f'<{alternate}>; rel="alternate"; type="application/ld+json"',
                },
                request=request,
            )
        if url == alternate:
            return httpx.Response(
                200,
                json={"@context": {"@vocab": "http://schema.org/"}},
                headers={"content-type": "application/ld+json"},
                request=request,
            )
        return httpx.Response(404, text="missing", request=request)

    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        document = await ensure_document_cached(root, client)
        again = await ensure_document_cached(root, client)

    assert document == {"@context": {"@vocab": "http://schema.org/"}}
    assert again == document
    assert hits.count(root) == 1
    assert hits.count(alternate) == 1


@pytest.mark.asyncio
async def test_materialize_unwraps_context_document_with_metadata_keys() -> None:
    root = "https://ctx.example/root.json"
    documents = {
        root: {
            "@context": {"@vocab": "http://schema.org/"},
            "comment": "JSON-LD context documents may carry metadata",
        }
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        return httpx.Response(200, json=documents[str(request.url)])

    payload: JsonObject = {"@context": root, "@id": "https://example.org/1"}
    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        materialized = await materialize_payload_contexts(payload, allowed_context_url=root, client=client)

    assert materialized["@context"] == {"@vocab": "http://schema.org/"}


@pytest.mark.asyncio
async def test_materialize_accepts_trailing_slash_variant() -> None:
    root = "https://schema.org/"
    documents = {
        root: {"@context": {"@vocab": "http://schema.org/"}},
        "https://schema.org": {"@context": {"@vocab": "http://schema.org/"}},
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        return httpx.Response(200, json=documents[str(request.url)])

    payload: JsonObject = {"@context": "https://schema.org", "@id": "https://example.org/1"}
    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        materialized = await materialize_payload_contexts(
            payload, allowed_context_url="https://schema.org/", client=client
        )

    assert materialized["@context"] == {"@vocab": "http://schema.org/"}


@pytest.mark.asyncio
async def test_materialize_http_pin_accepts_https_payload() -> None:
    documents = {
        "https://schema.org/": {"@context": {"@vocab": "http://schema.org/"}},
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        return httpx.Response(200, json=documents[str(request.url)])

    payload: JsonObject = {"@context": "https://schema.org/", "@id": "https://example.org/1"}
    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        materialized = await materialize_payload_contexts(
            payload, allowed_context_url="http://schema.org", client=client
        )

    assert materialized["@context"] == {"@vocab": "http://schema.org/"}


@pytest.mark.asyncio
async def test_materialize_https_pin_rejects_http_payload() -> None:
    hits = {"n": 0}

    async def handler(_request: httpx.Request) -> httpx.Response:
        hits["n"] += 1
        return httpx.Response(200, json={})

    payload: JsonObject = {"@context": "http://schema.org", "@id": "https://example.org/1"}
    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(ParserError, match="Remote JSON-LD @context"):
            await materialize_payload_contexts(payload, allowed_context_url="https://schema.org/", client=client)
    assert hits["n"] == 0


@pytest.mark.asyncio
async def test_materialize_accepts_context_list_with_allowlist() -> None:
    schema = "https://schema.org/"
    bios = "https://bioschemas.org/"
    documents = {
        schema: {"@context": {"@vocab": "http://schema.org/"}},
        bios: {"@context": {"Sample": "https://bioschemas.org/Sample"}},
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        return httpx.Response(200, json=documents[str(request.url)])

    payload: JsonObject = {
        "@context": [schema, bios],
        "@id": "https://example.org/1",
        "@type": "Dataset",
    }
    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        materialized = await materialize_payload_contexts(
            payload,
            allowed_context_url=[schema, bios],
            client=client,
        )

    assert materialized["@context"] == [
        {"@vocab": "http://schema.org/"},
        {"Sample": "https://bioschemas.org/Sample"},
    ]


@pytest.mark.asyncio
async def test_document_cache_evicts_when_over_cap() -> None:
    configure_document_cache_max_entries(2)
    hits: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        hits.append(str(request.url))
        return httpx.Response(200, json={"@context": {"n": str(request.url)}})

    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        for i in range(3):
            url = f"https://ctx.example/{i}.json"
            await ensure_document_cached(url, client)
        await ensure_document_cached("https://ctx.example/0.json", client)

    assert hits.count("https://ctx.example/0.json") == 2
    assert hits.count("https://ctx.example/1.json") == 1
    assert hits.count("https://ctx.example/2.json") == 1


@pytest.mark.asyncio
async def test_materialize_inlines_nested_context_without_top_level() -> None:
    root = "https://ctx.example/root.json"
    documents = {root: {"@context": {"@vocab": "http://schema.org/"}}}
    hits = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        hits["n"] += 1
        return httpx.Response(200, json=documents[str(request.url)])

    payload: JsonObject = {
        "@graph": [
            {
                "@context": root,
                "@id": "https://example.org/1",
                "@type": "Dataset",
                "name": "Nested",
            }
        ]
    }
    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        with pytest.raises(ParserError, match="HTTP client is required"):
            await materialize_payload_contexts(payload, allowed_context_url=root, client=None)
        materialized = await materialize_payload_contexts(payload, allowed_context_url=root, client=client)

    graph = materialized["@graph"]
    assert isinstance(graph, list)
    node = graph[0]
    assert isinstance(node, dict)
    assert node["@context"] == {"@vocab": "http://schema.org/"}
    assert hits["n"] == 1
