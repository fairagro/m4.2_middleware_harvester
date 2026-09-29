"""Unit tests for PhenoroamXmlParser."""

from __future__ import annotations

from pathlib import Path

import pytest

import middleware.parsing.register_builtin_parsers as _register_builtin_parsers
from middleware.parsing.discovery import UrlDiscoveryResult, XmlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser.phenoroam_xml import PhenoroamXmlParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.phenoroam.models import PhenoroamRecord

_ = _register_builtin_parsers

_FIXTURE = Path(__file__).parent / "fixtures" / "phenoroam_metadata_sample.xml"


def test_phenoroam_xml_parser_registered() -> None:
    parser_cls = PayloadParser.registry[ParserType.phenoroam_xml]
    assert parser_cls is PhenoroamXmlParser
    assert parser_cls.produces == PayloadKind.phenoroam_record


@pytest.mark.asyncio
async def test_phenoroam_xml_happy_path_without_client() -> None:
    xml = _FIXTURE.read_text(encoding="utf-8")
    payload = await PhenoroamXmlParser().parse(
        XmlDiscoveryResult(identifier="5bc8b6f0-b74b-4100-8211-a564c8f3d7c2", xml=xml),
        client=None,
        config=object(),
    )
    assert payload.kind == PayloadKind.phenoroam_record
    assert payload.identifier == "5bc8b6f0-b74b-4100-8211-a564c8f3d7c2"
    assert isinstance(payload.value, PhenoroamRecord)
    assert payload.value.title and "RGB-MiniplotBarley" in payload.value.title
    assert payload.value.item_uuid == "5bc8b6f0-b74b-4100-8211-a564c8f3d7c2"
    assert payload.value.responsible_contacts[0].name == "Marion Deichmann"
    assert payload.value.study is not None
    assert payload.value.study.investigation_title
    assert any("MiPlo_V2" in link for link in payload.value.datafile_links)


@pytest.mark.asyncio
async def test_phenoroam_xml_missing_metadata_raises() -> None:
    with pytest.raises(ParserError, match="Missing PhenoRoam XML"):
        await PhenoroamXmlParser().parse(
            XmlDiscoveryResult(identifier="empty", xml="  "),
            client=None,
            config=object(),
        )


@pytest.mark.asyncio
async def test_phenoroam_xml_wrong_root_raises() -> None:
    with pytest.raises(ParserError, match="Expected pr:metadataDataset"):
        await PhenoroamXmlParser().parse(
            XmlDiscoveryResult(identifier="bad-root", xml="<pr:other xmlns:pr='http://www.phenorob.de/'/>"),
            client=None,
            config=object(),
        )


@pytest.mark.asyncio
async def test_phenoroam_xml_rejects_url_discovery() -> None:
    with pytest.raises(ValueError, match="Unsupported discovery result type"):
        await PhenoroamXmlParser().parse(
            UrlDiscoveryResult("https://example.org/page"),
            client=None,
            config=object(),
        )
