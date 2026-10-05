"""Unit tests for the shared HTML+JSON-LD PayloadParser.

These exercise the parser directly, so ``middleware.parsing`` keeps owning the
tests for the code it owns (the ``linked_data`` HtmlJsonLdDataset tests cover
the shim on top of it, not this parser).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from middleware.harvester.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.parsing.discovery import JsonLdDiscoveryResult, UrlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.jsonld_context_loader import clear_context_document_cache
from middleware.parsing.parser.html_jsonld import HtmlJsonLdParser
from middleware.parsing.parser_config import ParserConfig
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind

PAGE_URL = "https://example.org/page"
_SCHEMA_ORG = "https://schema.org/"
_SCHEMA_ORG_ALLOW = [_SCHEMA_ORG]
_SCHEMA_ORG_DOC = {"@context": {"@vocab": "http://schema.org/"}}

SIMPLE_HTML = """
<html><head><script type="application/ld+json">
{"@context": "https://schema.org/", "@type": "Dataset", "name": "One"}
</script></head><body></body></html>
"""

MULTI_BLOCK_HTML = """
<html><head>
<script type="application/ld+json">
{"@context": "https://schema.org/", "@type": "Dataset", "name": "One"}
</script>
<script type="application/ld+json">
{"@context": "https://schema.org/", "@type": "Dataset", "name": "Two"}
</script>
</head><body></body></html>
"""

NO_JSONLD_HTML = "<html><head><title>No JSON-LD here</title></head><body></body></html>"

BAD_JSON_HTML = """
<html><head><script type="application/ld+json">{"@context": "https://schema.org/",</script></head></html>
"""

FOREIGN_CONTEXT_HTML = """
<html><head><script type="application/ld+json">
{"@context": "https://evil.example/ctx", "@type": "Dataset", "name": "One"}
</script></head></html>
"""


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_context_document_cache()


def _parser_config(*, jsonld_parse_threshold_bytes: int = 65536) -> ParserConfig:
    return ParserConfig(
        type=ParserType.html_jsonld,
        jsonld_parse_threshold_bytes=jsonld_parse_threshold_bytes,
        allowed_context_url=_SCHEMA_ORG_ALLOW,
    )


def _transport(html: str) -> httpx.MockTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="", headers={"content-type": "text/plain"})
        if request.url.host == "schema.org":
            return httpx.Response(200, json=_SCHEMA_ORG_DOC, headers={"content-type": "application/ld+json"})
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_parse_yields_rdf_graph_payload() -> None:
    async with NiceHttpClient(NiceHttpClientConfig(), transport=_transport(SIMPLE_HTML)) as client:
        payload = await HtmlJsonLdParser().parse(UrlDiscoveryResult(PAGE_URL), client=client, config=_parser_config())

    assert payload.kind == PayloadKind.rdf_graph
    assert payload.identifier == PAGE_URL
    assert len(payload.value) > 0  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_parse_merges_multiple_jsonld_blocks() -> None:
    async with NiceHttpClient(NiceHttpClientConfig(), transport=_transport(SIMPLE_HTML)) as client:
        single = await HtmlJsonLdParser().parse(UrlDiscoveryResult(PAGE_URL), client=client, config=_parser_config())
    clear_context_document_cache()
    async with NiceHttpClient(NiceHttpClientConfig(), transport=_transport(MULTI_BLOCK_HTML)) as client:
        merged = await HtmlJsonLdParser().parse(UrlDiscoveryResult(PAGE_URL), client=client, config=_parser_config())

    assert len(merged.value) > len(single.value)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_parse_rejects_non_url_discovery_result() -> None:
    async with NiceHttpClient(NiceHttpClientConfig(), transport=_transport(SIMPLE_HTML)) as client:
        with pytest.raises(ValueError, match="Unsupported discovery result type"):
            await HtmlJsonLdParser().parse(
                JsonLdDiscoveryResult(PAGE_URL, payload={}),
                client=client,
                config=_parser_config(),
            )


@pytest.mark.asyncio
async def test_parse_requires_an_http_client() -> None:
    with pytest.raises(ValueError, match="requires an HTTP client"):
        await HtmlJsonLdParser().parse(UrlDiscoveryResult(PAGE_URL), client=None, config=_parser_config())


@pytest.mark.asyncio
async def test_parse_wraps_fetch_failure_in_parser_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="", headers={"content-type": "text/plain"})
        raise httpx.ConnectError("connection refused")

    async with NiceHttpClient(NiceHttpClientConfig(), transport=httpx.MockTransport(handler)) as client:
        with (
            patch("middleware.harvester.nice_http_client.asyncio.sleep", new=AsyncMock()),
            pytest.raises(ParserError, match="Failed to fetch dataset URL"),
        ):
            await HtmlJsonLdParser().parse(UrlDiscoveryResult(PAGE_URL), client=client, config=_parser_config())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("html", "message"),
    [
        (NO_JSONLD_HTML, "No JSON-LD blocks found"),
        (BAD_JSON_HTML, "Invalid JSON in JSON-LD block"),
        (FOREIGN_CONTEXT_HTML, "Remote JSON-LD @context"),
    ],
)
async def test_graph_from_html_raises_parser_error(html: str, message: str) -> None:
    async with NiceHttpClient(NiceHttpClientConfig(), transport=_transport(html)) as client:
        with pytest.raises(ParserError, match=message):
            await HtmlJsonLdParser().graph_from_html(
                PAGE_URL,
                html,
                65536,
                client=client,
                allowed_context_url=_SCHEMA_ORG_ALLOW,
            )


@pytest.mark.asyncio
async def test_graph_from_html_offloads_blocks_over_threshold_to_thread() -> None:
    async with NiceHttpClient(NiceHttpClientConfig(), transport=_transport(SIMPLE_HTML)) as client:
        with patch(
            "middleware.parsing.parser.html_jsonld.asyncio.to_thread",
            new=AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)),
        ) as to_thread_mock:
            graph = await HtmlJsonLdParser().graph_from_html(
                PAGE_URL,
                SIMPLE_HTML,
                1,
                client=client,
                allowed_context_url=_SCHEMA_ORG_ALLOW,
            )

    assert to_thread_mock.called
    assert len(graph) > 0


@pytest.mark.asyncio
async def test_graph_from_html_parses_inline_when_under_threshold() -> None:
    async with NiceHttpClient(NiceHttpClientConfig(), transport=_transport(SIMPLE_HTML)) as client:
        with patch(
            "middleware.parsing.parser.html_jsonld.asyncio.to_thread",
            new=AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)),
        ) as to_thread_mock:
            graph = await HtmlJsonLdParser().graph_from_html(
                PAGE_URL,
                SIMPLE_HTML,
                65536,
                client=client,
                allowed_context_url=_SCHEMA_ORG_ALLOW,
            )

    assert not to_thread_mock.called
    assert len(graph) > 0
