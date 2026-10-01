"""Unit tests for the inline JsonLdParser."""

from __future__ import annotations

import pytest
from rdflib import Literal, URIRef
from rdflib.namespace import DCTERMS, RDF

import middleware.parsing.register_builtin_parsers as _register_builtin_parsers
from middleware.parsing.discovery import JsonLdDiscoveryResult, UrlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.jsonld import JsonLdParser
from middleware.parsing.parser.parser import PayloadParser
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


def test_jsonld_parser_registered_and_produces_rdf() -> None:
    parser_cls = PayloadParser.registry[ParserType.jsonld]
    assert parser_cls is JsonLdParser
    assert parser_cls.produces == PayloadKind.rdf_graph


@pytest.mark.asyncio
async def test_jsonld_parser_parses_inline_payload_to_graph() -> None:
    payload = await JsonLdParser().parse(
        JsonLdDiscoveryResult(identifier=_SUBJECT, payload=_PAYLOAD),
        client=None,
        config=None,
    )

    assert payload.kind == PayloadKind.rdf_graph
    assert payload.identifier == _SUBJECT
    assert (URIRef(_SUBJECT), DCTERMS.title, Literal("Dataset One")) in payload.value


@pytest.mark.asyncio
async def test_jsonld_parser_offloads_large_payload_to_thread() -> None:
    class _TinyThreshold:
        jsonld_parse_threshold_bytes = 1

    payload = await JsonLdParser().parse(
        JsonLdDiscoveryResult(identifier=_SUBJECT, payload=_PAYLOAD),
        client=None,
        config=_TinyThreshold(),
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
    ],
)
async def test_jsonld_parser_rejects_remote_context(context: object) -> None:
    payload: dict[str, object] = {"@context": context, "@id": _SUBJECT, "title": "Dataset One"}
    with pytest.raises(ParserError, match="Remote JSON-LD @context"):
        await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload), client=None, config=None
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "context",
    [
        "http://schema.org",
        "https://schema.org/",
        ["https://schema.org", {"sdoName": "http://schema.org/name"}],
    ],
)
async def test_jsonld_parser_localizes_schemaorg_context_without_fetching(
    context: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _no_fetch(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("remote @context must not be fetched")

    monkeypatch.setattr("rdflib.plugins.shared.jsonld.context.source_to_json", _no_fetch)
    payload: dict[str, object] = {"@context": context, "@id": _SUBJECT, "@type": "Dataset", "name": "Genome"}

    parsed = await JsonLdParser().parse(
        JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload), client=None, config=None
    )

    assert (URIRef(_SUBJECT), URIRef("http://schema.org/name"), Literal("Genome")) in parsed.value
    assert (URIRef(_SUBJECT), RDF.type, URIRef("http://schema.org/Dataset")) in parsed.value
    assert payload["@context"] == context


@pytest.mark.asyncio
async def test_jsonld_parser_rejects_remote_context_alongside_schemaorg() -> None:
    payload: dict[str, object] = {
        "@context": ["https://schema.org", "https://example.org/context.jsonld"],
        "@id": _SUBJECT,
        "name": "Genome",
    }
    with pytest.raises(ParserError, match="Remote JSON-LD @context"):
        await JsonLdParser().parse(
            JsonLdDiscoveryResult(identifier=_SUBJECT, payload=payload), client=None, config=None
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
