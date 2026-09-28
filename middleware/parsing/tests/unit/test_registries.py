"""Unit tests for shared PayloadParser registry."""

from __future__ import annotations

from collections.abc import Iterator
from typing import ClassVar, override

import pytest

import middleware.parsing.register_builtin_parsers as _register_builtin_parsers
from middleware.parsing.discovery import DiscoveryResult
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload

_ = _register_builtin_parsers


@pytest.fixture
def restore_registry() -> Iterator[None]:
    """Restore the builtin html_jsonld registration after a test overwrites it."""
    original = PayloadParser.registry[ParserType.html_jsonld]
    yield
    PayloadParser.registry[ParserType.html_jsonld] = original


def test_html_jsonld_parser_registered_and_produces_rdf() -> None:
    parser_cls = PayloadParser.registry[ParserType.html_jsonld]
    assert parser_cls.produces == PayloadKind.rdf_graph


@pytest.mark.usefixtures("restore_registry")
def test_register_stores_decorated_subclass_under_its_key() -> None:
    @PayloadParser.register(ParserType.html_jsonld)
    class _FakeParser(PayloadParser):
        produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

        @override
        async def parse(
            self,
            discovery_result: DiscoveryResult,
            client: object,
            config: object,
        ) -> ParsedPayload:
            del client, config
            return ParsedPayload(kind=PayloadKind.rdf_graph, value=object(), identifier=discovery_result.identifier)

    assert PayloadParser.registry[ParserType.html_jsonld] is _FakeParser
    assert _FakeParser.produces == PayloadKind.rdf_graph
