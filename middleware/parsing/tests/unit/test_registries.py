"""Unit tests for shared PayloadParser registry."""

from __future__ import annotations

from typing import ClassVar, override

import middleware.parsing.register_builtin_parsers as _register_builtin_parsers
from middleware.parsing.discovery import DiscoveryResult
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload

_ = _register_builtin_parsers


def test_html_jsonld_parser_registered_and_produces_rdf() -> None:
    parser_cls = PayloadParser.registry[ParserType.html_jsonld]
    assert parser_cls.produces == PayloadKind.rdf_graph


def test_parser_registry_accepts_new_registration() -> None:
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

    assert _FakeParser.produces == PayloadKind.rdf_graph
