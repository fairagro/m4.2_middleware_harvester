"""Unit tests for PhenoroamMapper."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import middleware.parsing.register_builtin_parsers as _register_parsers
import middleware.payload.register_builtin_mappers as _register_mappers
from middleware.parsing.discovery import XmlDiscoveryResult
from middleware.parsing.parser.phenoroam_xml import PhenoroamXmlParser
from middleware.payload.data_mapper import DataMapper
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperType
from middleware.payload.mapping_context import MappingContext
from middleware.payload.parsed_payload import ParsedPayload
from middleware.payload.phenoroam.mapper import PhenoroamMapper
from middleware.payload.phenoroam.models import PhenoroamPerson, PhenoroamRecord, PhenoroamStudyBlock

_ = (_register_parsers, _register_mappers)

_FIXTURE = Path(__file__).parent / "fixtures" / "phenoroam_metadata_sample.xml"


def test_phenoroam_mapper_registered() -> None:
    assert DataMapper.registry[MapperType.phenoroam_general] is PhenoroamMapper
    assert PhenoroamMapper.accepts == PayloadKind.phenoroam_record


def test_uuid_becomes_investigation_identifier() -> None:
    record = PhenoroamRecord(
        item_uuid="5bc8b6f0-b74b-4100-8211-a564c8f3d7c2",
        title="Dataset title",
        description="Desc",
        responsible_contacts=[
            PhenoroamPerson(name="Marion Deichmann", affiliation="INRES, University of Bonn"),
        ],
    )
    arc = PhenoroamMapper().map_record(record)
    assert arc.Identifier == "5bc8b6f0-b74b-4100-8211-a564c8f3d7c2"


def test_missing_uuid_falls_back_to_landing_url() -> None:
    record = PhenoroamRecord(title="Dataset title", description="Desc")
    ctx = MappingContext(harvest_source_id="catalog-id-123")
    arc = PhenoroamMapper().map_record(record, ctx)
    assert "phenoroam_phenorob_de" in arc.Identifier
    assert "catalog-id-123" in arc.Identifier


def test_map_sets_landing_page_as_harvested_source_url() -> None:
    record = PhenoroamRecord(item_uuid="abc-uuid", title="Dataset")
    harvested = next(
        iter(
            PhenoroamMapper().map(
                ParsedPayload(kind=PayloadKind.phenoroam_record, value=record, identifier="abc-uuid"),
                MappingContext(harvest_source_id="abc-uuid"),
            )
        )
    )
    assert harvested.source_url == (
        "https://phenoroam.phenorob.de/geonetwork/srv/eng/catalog.search#/metadata/abc-uuid"
    )


def test_contacts_split_and_affiliation() -> None:
    record = PhenoroamRecord(
        item_uuid="abc",
        title="T",
        responsible_contacts=[
            PhenoroamPerson(
                name="Marion Deichmann",
                email="m.deichmann@uni-bonn.de",
                affiliation="INRES, University of Bonn",
            ),
        ],
    )
    arc = PhenoroamMapper().map_record(record)
    contacts = list(arc.Contacts)
    assert len(contacts) == 1
    assert contacts[0].FirstName == "Marion"
    assert contacts[0].LastName == "Deichmann"
    assert contacts[0].Affiliation == "INRES, University of Bonn"


def test_empty_given_name_fails_closed() -> None:
    record = PhenoroamRecord(
        item_uuid="abc",
        title="T",
        responsible_contacts=[PhenoroamPerson(name="AcmeCorp")],
    )
    with pytest.raises(ValueError, match="non-empty given name"):
        PhenoroamMapper().map_record(record)


def test_study_investigation_nesting() -> None:
    record = PhenoroamRecord(
        item_uuid="abc",
        title="Dataset title",
        description="Dataset desc",
        study=PhenoroamStudyBlock(
            study_title="Study title",
            study_description="Study desc",
            investigation_title="Investigation title",
            investigation_description="Investigation desc",
        ),
    )
    arc = PhenoroamMapper().map_record(record)
    assert arc.Title == "Investigation title"
    assert arc.Description == "Investigation desc"
    study = next(iter(arc.Studies))
    assert study.Title == "Study title"
    assert study.Description == "Study desc"


def test_datafile_links_are_comments_not_file_outputs() -> None:
    record = PhenoroamRecord(
        item_uuid="abc-uuid",
        title="Dataset",
        datafile_links=[
            "https://phenoroam.phenorob.de/file-uploader/download/public/1.zip",
            "https://phenoroam.phenorob.de/file-uploader/download/public/2.zip",
        ],
    )
    harvested = next(
        iter(
            PhenoroamMapper().map(
                ParsedPayload(kind=PayloadKind.phenoroam_record, value=record, identifier="abc-uuid"),
                MappingContext(harvest_source_id="abc-uuid"),
            )
        )
    )
    crate = json.loads(harvested.arc_json)
    graph = crate["@graph"] if isinstance(crate, dict) and "@graph" in crate else crate
    file_nodes = [
        node
        for node in graph
        if isinstance(node, dict)
        and (
            node.get("@type") == "File"
            or (isinstance(node.get("@type"), list) and "File" in node["@type"])
            or (isinstance(node.get("@id"), str) and "/resources/" in node["@id"])
        )
    ]
    assert file_nodes == []
    # Comment column value must still mention the remote links in serialized JSON.
    blob = harvested.arc_json
    assert "file-uploader/download/public/1.zip" in blob
    assert "Raw Data" not in blob
    assert "Processed Data" not in blob


@pytest.mark.asyncio
async def test_fixture_round_trip_parse_and_map() -> None:
    xml = _FIXTURE.read_text(encoding="utf-8")
    payload = await PhenoroamXmlParser().parse(
        XmlDiscoveryResult(identifier="5bc8b6f0-b74b-4100-8211-a564c8f3d7c2", xml=xml),
        client=None,
        config=object(),
    )
    harvested = list(
        PhenoroamMapper().map(
            payload,
            MappingContext(harvest_source_id="5bc8b6f0-b74b-4100-8211-a564c8f3d7c2"),
        )
    )
    assert len(harvested) == 1
    assert harvested[0].identifier == "5bc8b6f0-b74b-4100-8211-a564c8f3d7c2"
    assert harvested[0].source_url == (
        "https://phenoroam.phenorob.de/geonetwork/srv/eng/catalog.search#/metadata/5bc8b6f0-b74b-4100-8211-a564c8f3d7c2"
    )
    assert harvested[0].studies == 1
    assert harvested[0].assays == 1
    assert "Marion" in harvested[0].arc_json
