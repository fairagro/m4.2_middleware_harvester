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
from middleware.payload.phenoroam.models import PhenoroamBBox, PhenoroamPerson, PhenoroamRecord, PhenoroamStudyBlock

_ = (_register_parsers, _register_mappers)

_FIXTURE = Path(__file__).parent / "fixtures" / "phenoroam_metadata_sample.xml"
_BBOX_FIXTURE = Path(__file__).parent / "fixtures" / "phenoroam_metadata_bbox.xml"


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


def test_keywords_map_to_study_annotation_table() -> None:
    record = PhenoroamRecord(
        item_uuid="abc-uuid",
        title="Dataset",
        keywords=["nutrient deficiency", "RGB image", "soil mini plots"],
    )
    harvested = next(
        iter(
            PhenoroamMapper().map(
                ParsedPayload(kind=PayloadKind.phenoroam_record, value=record, identifier="abc-uuid"),
                MappingContext(harvest_source_id="abc-uuid"),
            )
        )
    )
    assert "nutrient deficiency, RGB image, soil mini plots" in harvested.arc_json
    assert "Keywords" in harvested.arc_json


def test_bbox_maps_to_assay_geographic_comment() -> None:
    record = PhenoroamRecord(
        item_uuid="abc-uuid",
        title="Dataset",
        bbox=PhenoroamBBox(west="6.9895", east="6.9922", south="50.6152", north="50.6165"),
    )
    harvested = next(
        iter(
            PhenoroamMapper().map(
                ParsedPayload(kind=PayloadKind.phenoroam_record, value=record, identifier="abc-uuid"),
                MappingContext(harvest_source_id="abc-uuid"),
            )
        )
    )
    assert "Geographic Bounding Box" in harvested.arc_json
    assert "W:6.9895" in harvested.arc_json
    assert "E:6.9922" in harvested.arc_json
    assert "S:50.6152" in harvested.arc_json
    assert "N:50.6165" in harvested.arc_json


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
    assert "nutrient deficiency, RGB image, soil mini plots" in harvested[0].arc_json


@pytest.mark.asyncio
async def test_bbox_fixture_round_trip_parse_and_map() -> None:
    xml = _BBOX_FIXTURE.read_text(encoding="utf-8")
    payload = await PhenoroamXmlParser().parse(
        XmlDiscoveryResult(identifier="bbox-record", xml=xml),
        client=None,
        config=object(),
    )
    assert isinstance(payload.value, PhenoroamRecord)
    assert payload.value.bbox is not None
    assert payload.value.keywords
    harvested = list(
        PhenoroamMapper().map(
            payload,
            MappingContext(harvest_source_id=payload.identifier),
        )
    )
    assert len(harvested) == 1
    blob = harvested[0].arc_json
    assert "multi-temporal, orthomosaic, mixed cropping, rgb imagery" in blob
    assert "Geographic Bounding Box" in blob
    assert "W:6.9895" in blob
    assert "E:6.9922" in blob
    assert "S:50.6152" in blob
    assert "N:50.6165" in blob
    # Live PhenoRoam attachments use empty-port hosts (``phenoroam.phenorob.de:``); keep them.
    assert "Datafile Link" in blob
    assert "cka_04_02_RGB_A.zip" in blob


def test_empty_port_datafile_links_are_kept() -> None:
    """Empty port after host is a known PhenoRoam typo — do not drop datafile comments."""
    link = "https://phenoroam.phenorob.de:/geonetwork/srv/api/records/abc/attachments/file.zip"
    record = PhenoroamRecord(
        item_uuid="abc-uuid",
        title="Dataset",
        datafile_links=[link],
        thumbnail_url=link.replace("file.zip", "thumb.png"),
    )
    harvested = next(
        iter(
            PhenoroamMapper().map(
                ParsedPayload(kind=PayloadKind.phenoroam_record, value=record, identifier="abc-uuid"),
                MappingContext(harvest_source_id="abc-uuid"),
            )
        )
    )
    assert link in harvested.arc_json
    assert "Datafile Link" in harvested.arc_json
    assert "Thumbnail" in harvested.arc_json


def test_map_rejects_wrong_kind_eagerly() -> None:
    with pytest.raises(ValueError, match="phenoroam_record"):
        PhenoroamMapper().map(
            ParsedPayload(kind=PayloadKind.rdf_graph, value=object(), identifier="x"),
            MappingContext(),
        )
