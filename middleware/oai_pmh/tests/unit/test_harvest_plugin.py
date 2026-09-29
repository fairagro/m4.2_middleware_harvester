"""Unit tests for OAI ListRecords harvest helpers and plugin loop."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar, override
from unittest.mock import MagicMock, patch

import pytest
from rdflib import Graph

import middleware.parsing.register_builtin_parsers as _register_parsers
import middleware.payload.linked_data_mapper.register_builtins as _register_mappers
from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.plugin_base import HarvestedArc
from middleware.oai_pmh.config import Config
from middleware.oai_pmh.harvest import iter_discovery_units
from middleware.oai_pmh.plugin import OaiPmhPlugin
from middleware.parsing.discovery import DiscoveryResult, XmlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_config import ParserConfig
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.parsed_payload import ParsedPayload

_ = (_register_parsers, _register_mappers)

_FIXTURE = Path(__file__).parents[3] / "parsing" / "tests" / "unit" / "fixtures" / "minimal_rdf_xml.xml"


def _config(**overrides: object) -> Config:
    raw: dict[str, object] = {
        "endpoint_url": "https://example.org/oai",
        "metadata_prefix": "rdf",
        "respect_robots_txt": False,
    }
    raw.update(overrides)
    return Config.model_validate(raw)


def _parser_config() -> ParserConfig:
    return ParserConfig(type=ParserType.rdf_xml)


def _mapper_config() -> MapperConfig:
    return MapperConfig(type=MapperType.schema_org_general)


def _fake_record(*, identifier: str, deleted: bool = False, xml: str | None = None) -> MagicMock:
    record = MagicMock()
    record.header.identifier = identifier
    record.header.deleted = deleted
    record.deleted = deleted
    if deleted:
        return record

    body = xml or _FIXTURE.read_text(encoding="utf-8")
    # Drop XML declaration so the fragment can be embedded under <metadata>.
    if body.lstrip().startswith("<?xml"):
        body = body.split("?>", 1)[1].lstrip()
    record.raw = (
        f'<record xmlns="http://www.openarchives.org/OAI/2.0/">'
        f"<header><identifier>{identifier}</identifier></header>"
        f"<metadata>{body}</metadata></record>"
    )
    return record


def test_iter_discovery_units_unfiltered_and_deleted() -> None:
    records = [
        _fake_record(identifier="oai:ex:1"),
        _fake_record(identifier="oai:ex:del", deleted=True),
    ]
    scythe = MagicMock()
    scythe.list_records.return_value = iter(records)
    outcomes = list(iter_discovery_units(_config(), scythe=scythe))
    assert len(outcomes) == 2
    assert isinstance(outcomes[0], XmlDiscoveryResult)
    assert outcomes[0].identifier == "oai:ex:1"
    assert isinstance(outcomes[1], SkippedRecord)
    assert "deleted" in str(outcomes[1]).lower()
    scythe.list_records.assert_called_once_with(metadata_prefix="rdf", set_=None, ignore_deleted=False)


def test_iter_discovery_units_sequential_sets() -> None:
    scythe = MagicMock()

    def _by_set(**kwargs: object) -> Iterator[MagicMock]:
        set_ = kwargs.get("set_")
        yield _fake_record(identifier=f"oai:ex:{set_}")

    scythe.list_records.side_effect = _by_set
    outcomes = list(iter_discovery_units(_config(sets=["a", "b"]), scythe=scythe))
    assert [o.identifier for o in outcomes if isinstance(o, XmlDiscoveryResult)] == ["oai:ex:a", "oai:ex:b"]
    assert scythe.list_records.call_count == 2
    assert scythe.list_records.call_args_list[0].kwargs["set_"] == "a"
    assert scythe.list_records.call_args_list[1].kwargs["set_"] == "b"


@pytest.mark.asyncio
async def test_plugin_get_expected_datasets_none() -> None:
    plugin = OaiPmhPlugin(_config(), _mapper_config(), _parser_config())
    assert await plugin.get_expected_datasets() is None


@pytest.mark.asyncio
async def test_plugin_run_success_and_parser_error_continue() -> None:
    class _SelectiveParser(PayloadParser):
        produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

        @override
        async def parse(
            self,
            discovery_result: DiscoveryResult,
            client: object,
            config: object,
        ) -> ParsedPayload:
            _ = client, config
            if discovery_result.identifier.endswith(":bad"):
                raise ParserError("bad xml")
            return ParsedPayload(
                kind=PayloadKind.rdf_graph,
                value=Graph(),
                identifier=discovery_result.identifier,
            )

    stub_mapper = MagicMock()
    stub_mapper.accepts = PayloadKind.rdf_graph
    stub_mapper.map.return_value = [HarvestedArc(arc_json="mapped")]

    plugin = OaiPmhPlugin(_config(), _mapper_config(), _parser_config())
    plugin._parser_cls = _SelectiveParser  # noqa: SLF001
    plugin._mapper = stub_mapper  # noqa: SLF001

    units: list[XmlDiscoveryResult | SkippedRecord] = [
        XmlDiscoveryResult(identifier="oai:ex:bad", xml="<x/>"),
        XmlDiscoveryResult(identifier="oai:ex:good", xml=_FIXTURE.read_text(encoding="utf-8")),
        SkippedRecord("OAI record deleted: oai:ex:del", "oai:ex:del"),
    ]

    with patch.object(plugin, "_sync_discover", return_value=iter(units)):
        results = [item async for item in plugin.run()]

    errors = [r for r in results if isinstance(r, RecordProcessingError)]
    arcs = [r for r in results if isinstance(r, HarvestedArc)]
    skips = [r for r in results if isinstance(r, SkippedRecord)]
    assert len(errors) == 1
    assert len(arcs) == 1
    assert len(skips) == 1
    assert arcs[0].source_url == "oai:ex:good"


@pytest.mark.asyncio
async def test_plugin_kind_mismatch_record_error() -> None:
    class _OkParser(PayloadParser):
        produces: ClassVar[PayloadKind] = PayloadKind.rdf_graph

        @override
        async def parse(
            self,
            discovery_result: DiscoveryResult,
            client: object,
            config: object,
        ) -> ParsedPayload:
            _ = client, config
            return ParsedPayload(kind=PayloadKind.rdf_graph, value=Graph(), identifier=discovery_result.identifier)

    plugin = OaiPmhPlugin(_config(), _mapper_config(), _parser_config())
    plugin._parser_cls = _OkParser  # noqa: SLF001
    stub_mapper = MagicMock()
    stub_mapper.accepts = object()
    plugin._mapper = stub_mapper  # noqa: SLF001

    with patch.object(
        plugin,
        "_sync_discover",
        return_value=iter([XmlDiscoveryResult(identifier="oai:ex:1", xml="<rdf:RDF/>")]),
    ):
        results = [item async for item in plugin.run()]
    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)
    assert "incompatible" in str(results[0])
