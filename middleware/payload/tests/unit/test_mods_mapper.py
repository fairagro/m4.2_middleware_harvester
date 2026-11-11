"""Unit tests for ModsMapper."""

from __future__ import annotations

from pathlib import Path

import pytest

from middleware.parsing.parser.mods_xml import ModsXmlParser
from middleware.payload.mapping_context import MappingContext
from middleware.payload.mods.mapper import ModsMapper
from middleware.payload.mods.models import ModsName, ModsRecord
from middleware.payload.placeholders import PlaceholderConfig

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


def test_mods_mapper_maps_doi_licence_title_creators() -> None:
    record = ModsRecord(
        object_id="fixture_mods_1",
        title="Trap nest experiment data",
        abstract="Dataset abstract",
        doi="10.5073/20250926-163035-0",
        date_issued="2026-08-03",
        license_uri="http://www.mycore.org/classifications/mir_licenses#cc_by_4.0",
        names=[
            ModsName(
                given="Jana",
                family="Furtwengler",
                orcid="0009-0004-2610-6724",
                gnd="1256061514",
                affiliation="JKI",
                role_codes=["aut"],
            ),
            ModsName(given="Elias", family="Böckmann", orcid="0000-0002-4782-0714", role_codes=["aut"]),
        ],
        datafile_names=["Raw_data.xlsx"],
    )
    context = MappingContext(
        source_url="https://www.openagrar.de/receive/fixture_mods_1",
        harvest_source_id="fixture_mods_1",
    )
    arc = ModsMapper(PlaceholderConfig()).map_record(record, context)
    assert "Trap nest" in (arc.Title or "")
    assert arc.Description == "Dataset abstract"
    assert arc.Identifier == "fixture_mods_1"
    assert arc.Publications and arc.Publications[0].DOI == "10.5073/20250926-163035-0"
    assert len(list(arc.Contacts)) == 2
    assert arc.Contacts[0].FirstName == "Jana"
    assert arc.Contacts[0].ORCID == "0009-0004-2610-6724"
    assert any((r.Name or "").casefold() == "author" for r in arc.Contacts[0].Roles)
    assert arc.Publications[0].Authors == "J. Furtwengler; E. Böckmann"
    assert arc.License is not None
    assert "creativecommons.org/licenses/by/4.0" in arc.License.Content


def test_mods_mapper_openagrar_fixture_parity_fields() -> None:
    if not _FIXTURE_OBJECT.is_file():
        pytest.skip("OpenAgrar object fixture missing")
    record = ModsXmlParser().parse_object_xml(
        _FIXTURE_OBJECT.read_bytes(),
        discovery_identifier="openagrar_mods_00110150",
    )
    context = MappingContext(
        source_url="https://www.openagrar.de/receive/openagrar_mods_00110150",
        harvest_source_id="openagrar_mods_00110150",
    )
    arc = ModsMapper(PlaceholderConfig()).map_record(record, context)
    assert arc.Title and "Pemphredon lethifer" in arc.Title
    assert arc.Identifier == "openagrar_mods_00110150"
    assert arc.Publications and arc.Publications[0].DOI == "10.5073/20250926-163035-0"
    assert arc.License is not None
    assert "creativecommons.org/licenses/by/4.0" in arc.License.Content
    assert any(c.FirstName == "Jana" for c in arc.Contacts)
    assert arc.PublicReleaseDate == "2026-08-03"


def test_mods_mapper_refuses_missing_title() -> None:
    with pytest.raises(ValueError, match="no title"):
        ModsMapper().map_record(ModsRecord(object_id="x", doi="10.1/x"))


def test_mods_keywords_become_investigation_comments() -> None:
    record = ModsRecord(
        object_id="fixture_mods_kw",
        title="Keyworded dataset",
        keywords=["Soil", "soil", "Water"],
    )
    context = MappingContext(
        source_url="https://www.openagrar.de/receive/fixture_mods_kw",
        harvest_source_id="fixture_mods_kw",
    )
    arc = ModsMapper(PlaceholderConfig()).map_record(record, context)
    by_name = {c.Name: c.Value for c in arc.Comments if c.Name}
    assert by_name["Keywords"] == "Soil, Water"
    assert by_name["keyword [Soil]"] == "Soil"
    assert by_name["keyword [Water]"] == "Water"
    assert "keyword [soil]" not in by_name
    assert all(table.Name != "Data Collection" for study in arc.Studies for table in study.Tables)
