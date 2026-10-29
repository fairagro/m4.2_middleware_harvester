"""Unit tests for ModsXmlParser."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from middleware.contracts.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.parsing.discovery import UrlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.mods_xml import ModsXmlParser
from middleware.payload.kinds import PayloadKind
from middleware.payload.mods.models import ModsRecord

_TEST_HTTP = NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None)

_FIXTURE_OBJECT = (
    Path(__file__).resolve().parents[4]
    / "dev_environment"
    / "fixtures"
    / "openagrar"
    / "api"
    / "v2"
    / "objects"
    / "openagrar_mods_00110150"
)

_MINIMAL_OBJECT = """<?xml version="1.0" encoding="UTF-8"?>
<mycoreobject ID="fixture_mods_1">
  <metadata>
    <def.modsContainer>
      <modsContainer>
        <mods:mods xmlns:mods="http://www.loc.gov/mods/v3"
                   xmlns:xlink="http://www.w3.org/1999/xlink">
          <mods:titleInfo>
            <mods:title>Example MODS Title</mods:title>
          </mods:titleInfo>
          <mods:abstract>Short abstract.</mods:abstract>
          <mods:identifier type="doi">10.1234/example</mods:identifier>
          <mods:originInfo>
            <mods:dateIssued>2024-01-15</mods:dateIssued>
          </mods:originInfo>
          <mods:accessCondition type="use and reproduction"
            xlink:href="http://www.mycore.org/classifications/mir_licenses#cc_by_4.0"/>
          <mods:name type="personal">
            <mods:namePart type="family">Doe</mods:namePart>
            <mods:namePart type="given">Jane</mods:namePart>
            <mods:nameIdentifier type="orcid">0000-0001-2345-6789</mods:nameIdentifier>
            <mods:affiliation>Example Institute</mods:affiliation>
          </mods:name>
        </mods:mods>
      </modsContainer>
    </def.modsContainer>
  </metadata>
  <structure>
    <derobjects>
      <derobject>
        <maindoc>data.csv</maindoc>
      </derobject>
    </derobjects>
  </structure>
</mycoreobject>
"""


def test_mods_xml_parser_happy_path_from_bytes() -> None:
    parser = ModsXmlParser()
    record = parser.parse_object_xml(_MINIMAL_OBJECT, discovery_identifier="fixture_mods_1")
    assert isinstance(record, ModsRecord)
    assert record.object_id == "fixture_mods_1"
    assert record.title == "Example MODS Title"
    assert record.abstract == "Short abstract."
    assert record.doi == "10.1234/example"
    assert record.date_issued == "2024-01-15"
    assert record.license_uri == "http://www.mycore.org/classifications/mir_licenses#cc_by_4.0"
    assert record.names[0].given == "Jane"
    assert record.names[0].family == "Doe"
    assert record.names[0].orcid == "0000-0001-2345-6789"
    assert record.datafile_names == ["data.csv"]


def test_mods_xml_parser_openagrar_fixture() -> None:
    if not _FIXTURE_OBJECT.is_file():
        pytest.skip("OpenAgrar object fixture missing")
    parser = ModsXmlParser()
    record = parser.parse_object_xml(
        _FIXTURE_OBJECT.read_bytes(),
        discovery_identifier="openagrar_mods_00110150",
    )
    assert "Pemphredon lethifer" in (record.title or "")
    assert record.doi == "10.5073/20250926-163035-0"
    assert record.date_issued == "2026-08-03"
    assert "cc_by_4.0" in (record.license_uri or "")
    assert len(record.names) >= 2
    assert "pith diameter" in (record.abstract or "").lower()


def test_mods_xml_parser_requires_client_for_url() -> None:
    parser = ModsXmlParser()

    async def run() -> None:
        await parser.parse(
            UrlDiscoveryResult("https://example.org/api/v2/objects/x"),
            client=None,
            config=object(),
        )

    with pytest.raises(ValueError, match="HTTP client"):
        asyncio.run(run())


def test_mods_xml_parser_missing_mods_fails() -> None:
    parser = ModsXmlParser()
    with pytest.raises(ParserError, match="No mods:mods"):
        parser.parse_object_xml(
            b'<?xml version="1.0"?><mycoreobject ID="x"><metadata/></mycoreobject>',
            discovery_identifier="x",
        )


def test_mods_xml_parser_does_not_expand_external_entities() -> None:
    """Hardened parser must not expand internal entities into element text."""
    evil = b"""<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY a "EXPANDED">]>
<mycoreobject ID="evil">
  <metadata>
    <mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
      <mods:titleInfo><mods:title>&a;</mods:title></mods:titleInfo>
    </mods:mods>
  </metadata>
</mycoreobject>
"""
    parser = ModsXmlParser()
    record = parser.parse_object_xml(evil, discovery_identifier="evil")
    assert "EXPANDED" not in (record.title or "")


def test_mods_xml_parser_fetches_url() -> None:
    parser = ModsXmlParser()

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_MINIMAL_OBJECT.encode("utf-8"))

    transport = httpx.MockTransport(handler)

    async def run() -> ModsRecord:
        async with NiceHttpClient(_TEST_HTTP, transport=transport) as client:
            payload = await parser.parse(
                UrlDiscoveryResult(
                    "https://example.org/api/v2/objects/fixture_mods_1",
                    harvest_source_id="fixture_mods_1",
                ),
                client=client,
                config=object(),
            )
        assert payload.kind == PayloadKind.mods_record
        assert isinstance(payload.value, ModsRecord)
        return payload.value

    record = asyncio.run(run())
    assert record.title == "Example MODS Title"
