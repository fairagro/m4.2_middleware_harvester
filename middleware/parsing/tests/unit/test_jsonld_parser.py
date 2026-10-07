"""Unit tests for the inline JsonLdParser."""

from __future__ import annotations

import httpx
import pytest
from rdflib import Literal, URIRef
from rdflib.namespace import DCTERMS, RDF

import middleware.parsing.register_builtin_parsers as _register_builtin_parsers
from middleware.contracts.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.parsing.discovery import JsonLdDiscoveryResult, UrlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.jsonld_context_loader import clear_context_document_cache
from middleware.parsing.parser.jsonld import JsonLdParser
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_config import ParserConfig
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind

_ = _register_builtin_parsers

_SUBJECT = "https://example.org/dataset/1"
_PAYLOAD: dict[str, object] = {
    "@graph": [
        {
            "@id": _SUBJECT,
            "@type": ["http://www.w3.org/ns/dcat#Dataset"],
            "http://purl.org/dc/terms/title": [{"@value": "Dataset One"}],
        },
    ],
}
_SCHEMA_ORG = "https://schema.org/"
_SCHEMA_ORG_ALLOW = [_SCHEMA_ORG]
_SCHEMA_ORG_DOC = {"@context": {"@vocab": "http://schema.org/"}}


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_context_document_cache()


def test_jsonld_parser_registered_and_produces_rdf() -> None:
    parser_cls = PayloadParser.registry[ParserType.jsonld]
    assert parser_cls is JsonLdParser
    assert parser_cls.produces == PayloadKind.rdf_graph


@pytest.mark.asyncio
async def test_jsonld_parser_parses_inline_payload_to_graph() -> None:
    payload = await JsonLdParser().parse(
        JsonLdDiscoveryResult(identifier=_SUBJECT, payload=_PAYLOAD),
        client=None,
        config=ParserConfig(type=ParserType.jsonld),
    )

    assert payload.kind == PayloadKind.rdf_graph
    assert payload.identifier == _SUBJECT
    assert (URIRef(_SUBJECT), DCTERMS.title, Literal("Dataset One")) in payload.value


@pytest.mark.asyncio
async def test_jsonld_parser_offloads_large_payload_to_thread() -> None:
    payload = await JsonLdParser().parse(
        JsonLdDiscoveryResult(identifier=_SUBJECT, payload=_PAYLOAD),
        client=None,
        config=ParserConfig(type=ParserType.jsonld, jsonld_parse_threshold_bytes=1),
    )

    assert len(payload.value) == 2


@pytest.mark.asyncio
async def test_jsonld_parser_rejects_other_discovery_result_types() -> None:
    with pytest.raises(ValueError, match="Unsupported discovery result"):
        await JsonLdParser().parse(UrlDiscoveryResult("https://example.org/page"), client=None, config=None)


@pytest.mark.asyncio
async def test_jsonld_parser_rejects_empty_payload() -> None:
    with pytest.raises(ParserError, match="Missing JSON-LD payload"):
        await JsonLdParser().parse(JsonLdDiscoveryResult(identifier=_SUBJECT, payload={}), client=None, config=None)


@pytest.mark.asyncio
async def test_jsonld_parser_rejects_payload_yielding_empty_graph() -> None:
    with pytest.raises(ParserError, match="empty graph"):
        await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier=_SUBJECT, payload={"@graph": []}),
            client=None,
            config=None,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "context",
    [
        "https://example.org/context.jsonld",
        ["https://example.org/context.jsonld", {"title": "http://purl.org/dc/terms/title"}],
        {"@import": "https://example.org/context.jsonld"},
        "http://schema.org",
        "https://schema.org/",
    ],
)
async def test_jsonld_parser_requires_client_for_remote_context_when_unset(context: object) -> None:
    payload: dict[str, object] = {"@context": context, "@id": _SUBJECT, "title": "Dataset One"}
    with pytest.raises(ParserError, match="HTTP client is required"):
        await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload),
            client=None,
            config=ParserConfig(type=ParserType.jsonld),
        )


@pytest.mark.asyncio
async def test_jsonld_parser_fetches_remote_context_when_unset() -> None:
    hits = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        hits["n"] += 1
        return httpx.Response(200, json=_SCHEMA_ORG_DOC)

    payload: dict[str, object] = {
        "@context": _SCHEMA_ORG,
        "@id": _SUBJECT,
        "@type": "Dataset",
        "name": "Genome",
    }

    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        parsed = await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload),
            client=client,
            config=ParserConfig(type=ParserType.jsonld),
        )
        await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload),
            client=client,
            config=ParserConfig(type=ParserType.jsonld),
        )

    assert (URIRef(_SUBJECT), URIRef("http://schema.org/name"), Literal("Genome")) in parsed.value
    assert hits["n"] == 1


@pytest.mark.asyncio
async def test_jsonld_parser_resolves_allowlisted_schemaorg_context() -> None:
    hits = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        hits["n"] += 1
        return httpx.Response(200, json=_SCHEMA_ORG_DOC)

    payload: dict[str, object] = {
        "@context": _SCHEMA_ORG,
        "@id": _SUBJECT,
        "@type": "Dataset",
        "name": "Genome",
    }
    config = ParserConfig(type=ParserType.jsonld, allowed_context_url=_SCHEMA_ORG_ALLOW)

    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        parsed = await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload),
            client=client,
            config=config,
        )
        await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload),
            client=client,
            config=config,
        )

    assert (URIRef(_SUBJECT), URIRef("http://schema.org/name"), Literal("Genome")) in parsed.value
    assert (URIRef(_SUBJECT), RDF.type, URIRef("http://schema.org/Dataset")) in parsed.value
    assert hits["n"] == 1
    assert payload["@context"] == _SCHEMA_ORG


@pytest.mark.asyncio
async def test_jsonld_parser_requires_client_for_remote_context() -> None:
    payload: dict[str, object] = {"@context": _SCHEMA_ORG, "@id": _SUBJECT, "name": "Genome"}
    with pytest.raises(ParserError, match="HTTP client is required"):
        await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload),
            client=None,
            config=ParserConfig(type=ParserType.jsonld, allowed_context_url=_SCHEMA_ORG_ALLOW),
        )


@pytest.mark.asyncio
async def test_jsonld_parser_accepts_inline_context() -> None:
    payload: dict[str, object] = {
        "@context": {"title": "http://purl.org/dc/terms/title"},
        "@id": _SUBJECT,
        "title": "Dataset One",
    }
    parsed = await JsonLdParser().parse(
        JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload),
        client=None,
        config=None,
    )

    assert (URIRef(_SUBJECT), DCTERMS.title, Literal("Dataset One")) in parsed.value


@pytest.mark.asyncio
async def test_jsonld_parser_turns_bare_doi_id_into_doi_iri() -> None:
    """Bare DOI ``@id`` must become ``https://doi.org/…`` before rdflib expands relative IRIs (#416)."""
    hits = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        hits["n"] += 1
        return httpx.Response(200, json=_SCHEMA_ORG_DOC)

    payload: dict[str, object] = {
        "@context": "http://schema.org",
        "@id": "10.5447/ipk/2011/0",
        "@type": "Dataset",
        "name": "D",
    }
    async with NiceHttpClient(
        NiceHttpClientConfig(respect_robots_txt=False), transport=httpx.MockTransport(handler)
    ) as client:
        parsed = await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier="edal", payload=payload),
            client=client,
            config=ParserConfig(type=ParserType.jsonld, allowed_context_url=["http://schema.org"]),
        )

    assert (
        URIRef("https://doi.org/10.5447/ipk/2011/0"),
        RDF.type,
        URIRef("http://schema.org/Dataset"),
    ) in parsed.value
    assert hits["n"] == 1
