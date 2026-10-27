"""Unit tests for InspireMapper DataMapper.map harvest path."""

from __future__ import annotations

import json

import pytest
from arctrl import ARC, ArcInvestigation  # type: ignore[import-untyped]

from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.inspire.mapper import InspireMapper
from middleware.payload.inspire.models import Contact, InspireRecord, ResourceIdentifier
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig
from middleware.payload.mapping_context import MappingContext
from middleware.payload.parsed_payload import ParsedPayload


def _minimal_record(**kwargs: object) -> InspireRecord:
    defaults: dict[str, object] = {
        "identifier": "uuid-map-1",
        "title": "Mapped Dataset",
        "abstract": "Abstract",
        "keywords": [],
        "topic_categories": [],
        "contacts": [],
        "constraints": [],
        "resource_identifiers": [],
        "resource_language": [],
        "graphic_overviews": [],
        "dates": [],
        "spatial_resolution_denominators": [],
        "spatial_resolution_distances": [],
        "creators": [],
        "publishers": [],
        "contributors": [],
        "access_constraints": [],
        "use_constraints": [],
        "classification": [],
        "other_constraints": [],
        "other_constraints_url": [],
        "distribution_formats": [],
        "online_resources": [],
        "conformance_results": [],
        "reference_systems": [],
    }
    defaults.update(kwargs)
    return InspireRecord.model_validate(defaults)


def test_map_yields_harvested_arc_with_source_url_and_counts() -> None:
    record = _minimal_record()
    harvested = next(
        iter(
            InspireMapper().map(
                ParsedPayload(kind=PayloadKind.inspire_record, value=record, identifier=record.identifier),
                MappingContext(source_url="https://csw.example.org/record/uuid-map-1"),
            )
        )
    )
    assert isinstance(harvested, HarvestedArc)
    assert harvested.source_url == "https://csw.example.org/record/uuid-map-1"
    assert harvested.identifier == "uuid-map-1"
    assert harvested.studies == 1
    assert harvested.assays == 1
    assert harvested.arc_json


def test_map_omits_source_url_when_context_has_none() -> None:
    record = _minimal_record()
    harvested = next(
        iter(
            InspireMapper().map(
                ParsedPayload(kind=PayloadKind.inspire_record, value=record, identifier=record.identifier),
                MappingContext(),
            )
        )
    )
    assert harvested.source_url is None
    assert harvested.identifier == "uuid-map-1"


def test_map_rejects_wrong_kind() -> None:
    with pytest.raises(ValueError, match="inspire_record"):
        next(
            iter(
                InspireMapper().map(
                    ParsedPayload(kind=PayloadKind.rdf_graph, value=object(), identifier="x"),
                    MappingContext(),
                )
            )
        )


def test_publication_authors_survive_ro_crate_serialization() -> None:
    """Authors use "F. Last" so the RO-Crate writer's comma split cannot fragment them (#420)."""
    record = _minimal_record(
        contacts=[
            Contact(name="John Doe", organization="Test Org", role="author"),
            Contact(name="Rita Roe", organization="Test Org", role="author"),
        ],
        resource_identifiers=[ResourceIdentifier(code="10.1234/doi", codespace="DOI")],
    )
    harvested = next(
        iter(
            InspireMapper().map(
                ParsedPayload(kind=PayloadKind.inspire_record, value=record, identifier=record.identifier),
                MappingContext(source_url="https://csw.example.org/record/uuid-map-1"),
            )
        )
    )

    author_ids = [
        item["@id"]
        for item in json.loads(harvested.arc_json)["@graph"]
        if str(item.get("@id", "")).startswith("#Author_")
    ]
    assert author_ids == ["#Author_J. Doe; R. Roe"]


# --- dataset date (#408) ----------------------------------------------------


def test_bonares_citation_publication_date_not_date_stamp() -> None:
    """BonaRes 00015394-…: dateStamp 2026-08-18 (metadata), citation publication 2026-05-19."""
    record = _minimal_record(
        date_stamp="2026-08-18T07:29:17Z",
        dates=[{"date": "2026-05-19T09:13:00Z", "datetype": "publication"}],
    )
    arc = InspireMapper().map_record(record)

    assert arc.PublicReleaseDate == "2026-05-19T09:13:00Z"
    assert arc.Studies[0].PublicReleaseDate == "2026-05-19T09:13:00Z"
    assert not arc.SubmissionDate
    assert [(c.Name, c.Value) for c in arc.Comments if c.Name == "Metadata Date"] == [
        ("Metadata Date", "2026-08-18T07:29:17Z")
    ]


@pytest.mark.parametrize(
    ("dates", "expected"),
    [
        (
            [("2021-01-01", "creation"), ("2023-05-01", "publication"), ("2022-03-01", "publication")],
            "2022-03-01",
        ),
        ([("2021-01-01", "creation"), ("2024-02-01", "revision"), ("2025-02-01", "revision")], "2025-02-01"),
        ([("2021-06-01", "creation"), ("2020-06-01", "creation")], "2020-06-01"),
        ([("2021-06-01", None)], None),
        ([], None),
    ],
)
def test_release_date_order_publication_revision_creation(
    dates: list[tuple[str, str | None]], expected: str | None
) -> None:
    record = _minimal_record(
        date_stamp="2026-08-18",
        dates=[{"date": date, "datetype": datetype} for date, datetype in dates],
    )
    arc = InspireMapper().map_record(record)
    assert (arc.PublicReleaseDate or None) == expected


@pytest.mark.parametrize(
    ("dates", "expected"),
    [
        ([("2023-05-01", "publication"), ("2021-06-01", "creation"), ("2020-06-01", "creation")], "2020-06-01"),
        ([("2023-05-01", "publication"), ("2024-02-01", "revision")], None),
    ],
)
def test_creation_date_is_submission_date(dates: list[tuple[str, str]], expected: str | None) -> None:
    """Only a citation ``creation`` date becomes RO-Crate dateCreated (#407)."""
    record = _minimal_record(
        date_stamp="2026-08-18",
        dates=[{"date": date, "datetype": datetype} for date, datetype in dates],
    )
    arc = InspireMapper().map_record(record)
    assert (arc.SubmissionDate or None) == expected
    assert (arc.Studies[0].SubmissionDate or None) == expected


# --- DOI normalisation (#410) -----------------------------------------------


def test_geonode_doi_is_bare_and_deduplicated_in_ro_crate() -> None:
    """BonaRes 00de8e8c-…: ``doi:https://doi.org/…`` must not become ``https://dx.doi.org/https://…``."""
    record = _minimal_record(
        resource_identifiers=[
            ResourceIdentifier(
                code="doi:https://doi.org/10.4228/zalf.vjcp-vep3",
                url="https://dx.doi.org/https://doi.org/10.4228/zalf.vjcp-vep3",
            ),
            ResourceIdentifier(code="https://doi.org/10.4228/ZALF.VJCP-VEP3"),
            ResourceIdentifier(code="doi:https://www.ncbi.nlm.nih.gov/search/all/?term=PRJNA1140101"),
            ResourceIdentifier(code="978-3-16-148410-0", codespace="ISBN"),
        ],
    )
    harvested = next(
        iter(
            InspireMapper().map(
                ParsedPayload(kind=PayloadKind.inspire_record, value=record, identifier=record.identifier),
                MappingContext(source_url="https://csw.example.org/record/uuid-map-1"),
            )
        )
    )

    graph = json.loads(harvested.arc_json)["@graph"]
    citation_ids = [
        ident["@id"]
        for item in graph
        if item.get("@type") == "ScholarlyArticle"
        for ident in (item["identifier"] if isinstance(item["identifier"], list) else [item["identifier"]])
    ]
    assert citation_ids == ["10.4228/zalf.vjcp-vep3"]


# --- organisational creators (#411) -----------------------------------------


def test_thuenen_organisation_creator_survives_ro_crate_round_trip() -> None:
    """Thünen Atlas: every contact is an organisation; originator/author become ``Creator Organization``."""
    org = "Thünen-Institut Zentrum für Informationsmanagement"
    url = "https://www.thuenen.de/"
    record = _minimal_record(
        contacts=[
            Contact(organization=org, organization_url=url, role="originator"),
            Contact(organization=org, organization_url=url, role="author"),
            Contact(organization=org, role="pointOfContact"),
            Contact(organization="BonaRes Data Centre", role="owner"),
        ],
        creators=[Contact(organization=org.upper(), role="originator")],
    )
    harvested = next(
        iter(
            InspireMapper().map(
                ParsedPayload(kind=PayloadKind.inspire_record, value=record, identifier=record.identifier),
                MappingContext(source_url="https://csw.example.org/record/uuid-map-1"),
            )
        )
    )

    arc = ARC.from_rocrate_json_string(harvested.arc_json)
    assert not list(arc.Contacts)
    assert [(c.Name, c.Value) for c in arc.Comments if c.Name.startswith(("Creator", "Point", "Owner"))] == [
        ("Creator Organization", org),
        ("Creator Organization URL", url),
        ("Point of Contact", org),
        ("Owner", "BonaRes Data Centre"),
    ]


# Every individualName DWD publishes through GDI-DE (live harvest 2026-10-12, #393): departments, not people.
DWD_DEPARTMENTS = [
    "KU31 Agrarmeteorologie",
    "Referat Hydrometeorologische Beratungsleistungen (KU41)",
    "Zentrales Klimabüro",
    "Satellitengestütztes Klimamonitoring - DUETT",
    "CDC - Vertrieb Klima und Umwelt",
]
DWD = "Deutscher Wetterdienst"


def _contact_comments(inv: ArcInvestigation) -> list[tuple[str, str]]:
    names = ("Point of Contact", "Creator Organization")
    return [(c.Name, c.Value) for c in inv.Comments if c.Name in names]


@pytest.mark.parametrize("department", DWD_DEPARTMENTS)
def test_individual_name_as_organisation_becomes_comment(department: str) -> None:
    record = _minimal_record(contacts=[Contact(name=department, organization=DWD, role="pointOfContact")])

    inv = InspireMapper(individual_name_is_organisation=True).map_investigation(record)

    assert not list(inv.Contacts)
    assert _contact_comments(inv) == [("Point of Contact", f"{DWD} ({department})")]


def test_individual_name_as_organisation_creator_is_creator_organization() -> None:
    record = _minimal_record(creators=[Contact(name="Zentrales Klimabüro", organization=DWD, role="originator")])

    inv = InspireMapper(individual_name_is_organisation=True).map_investigation(record)

    assert not list(inv.Contacts)
    assert _contact_comments(inv) == [("Creator Organization", f"{DWD} (Zentrales Klimabüro)")]


def test_department_name_is_person_by_default() -> None:
    """Without the setting a multi-word individualName still maps as a Person (unchanged behaviour)."""
    record = _minimal_record(contacts=[Contact(name="KU31 Agrarmeteorologie", organization=DWD, role="pointOfContact")])

    inv = InspireMapper().map_investigation(record)

    assert len(list(inv.Contacts)) == 1


def test_from_config_passes_individual_name_is_organisation() -> None:
    config = MapperConfig.model_validate({
        "inspire_general": {"individual_name_is_organisation": True},
    })
    record = _minimal_record(contacts=[Contact(name="Jane Doe", role="pointOfContact")])

    inv = InspireMapper.from_config(config).map_investigation(record)

    assert not list(inv.Contacts)


# --- no invented data files (#353) ------------------------------------------


def _bonares_style_record() -> InspireRecord:
    return _minimal_record(
        temporal_extent=("2000-01-01", "2020-12-31"),
        dates=[
            {"date": "2019-03-01", "datetype": "creation"},
            {"date": "2021-05-19", "datetype": "publication"},
        ],
        lineage="Field trial data were aggregated per plot.",
        conformance_results=[{"specification_title": "INSPIRE", "degree": "true"}],
        distribution_formats=[{"name": "GeoJSON", "version": "1.0"}],
    )


def test_study_protocols_do_not_invent_data_files_in_ro_crate() -> None:
    harvested = next(
        iter(
            InspireMapper().map(
                ParsedPayload(kind=PayloadKind.inspire_record, value=_bonares_style_record(), identifier="uuid-map-1"),
                MappingContext(source_url="https://csw.example.org/record/uuid-map-1"),
            )
        )
    )

    invented = [
        item["@id"]
        for item in json.loads(harvested.arc_json)["@graph"]
        if item.get("@type") == "File" and str(item.get("@id", "")).endswith(("Raw Data", "Processed Data"))
    ]
    assert invented == []


def test_study_protocols_keep_their_parameters() -> None:
    study = InspireMapper().map_study(_bonares_style_record())

    parameters = {
        table.Name: [
            (col.header.ToTerm().Name, col.cells[0].AsTerm.Name) for col in table.Columns if col.header.is_parameter
        ]
        for table in study.Tables
        if table.Name in {"Data Acquisition", "Data Processing"}
    }
    assert parameters == {
        "Data Acquisition": [
            ("Temporal Extent", "2000-01-01 to 2020-12-31"),
            ("Acquisition Date", "2019-03-01"),
        ],
        "Data Processing": [
            ("Processing Description", "Field trial data were aggregated per plot."),
            ("Conformance", "INSPIRE: PASS"),
            ("Output Format", "GeoJSON v1.0"),
            ("Processing Date", "2021-05-19"),
        ],
    }


def test_non_geographic_record_has_no_dangling_selected_location() -> None:
    record = _minimal_record(hierarchy="nonGeographicDataset", temporal_extent=("2000-01-01", "2020-12-31"))
    mapper = InspireMapper()

    study = mapper.map_study(record)

    acquisition = next(table for table in study.Tables if table.Name == "Data Acquisition")
    assert not any(col.header.is_input for col in acquisition.Columns)
    harvested = next(
        iter(
            mapper.map(
                ParsedPayload(kind=PayloadKind.inspire_record, value=record, identifier="uuid-map-1"),
                MappingContext(source_url="https://csw.example.org/record/uuid-map-1"),
            )
        )
    )
    selected = [item["@id"] for item in json.loads(harvested.arc_json)["@graph"] if "Selected Location" in str(item)]
    assert selected == []


def test_geographic_record_without_spatial_info_has_no_dangling_selected_location() -> None:
    record = _minimal_record(hierarchy="dataset", temporal_extent=("2000-01-01", "2020-12-31"))

    study = InspireMapper().map_study(record)

    names = [table.Name for table in study.Tables]
    assert "Spatial Sampling" not in names
    acquisition = next(table for table in study.Tables if table.Name == "Data Acquisition")
    assert not any(col.header.is_input for col in acquisition.Columns)


def test_geographic_record_with_bbox_keeps_spatial_sampling_to_acquisition_link() -> None:
    record = _minimal_record(
        hierarchy="dataset",
        spatial_extent=[10.0, 48.0, 11.0, 49.0],
        temporal_extent=("2000-01-01", "2020-12-31"),
    )

    study = InspireMapper().map_study(record)

    tables = {table.Name: table for table in study.Tables}
    sampling_outputs = [col.cells[0].AsFreeText for col in tables["Spatial Sampling"].Columns if col.header.is_output]
    acquisition_inputs = [col.cells[0].AsFreeText for col in tables["Data Acquisition"].Columns if col.header.is_input]
    assert sampling_outputs == ["Selected Location"]
    assert acquisition_inputs == ["Selected Location"]


def test_creation_date_alone_does_not_create_data_processing_protocol() -> None:
    record = _minimal_record(dates=[{"date": "2019-03-01", "datetype": "creation"}])

    study = InspireMapper().map_study(record)

    assert "Data Processing" not in [table.Name for table in study.Tables]


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"dataset_uri": "https://data.example.com/api"}, "https://data.example.com/api"),
        ({"online_resources": [{"url": "https://data.example.com/download"}]}, "https://data.example.com/download"),
    ],
)
def test_assay_output_uri_is_unchanged(overrides: dict[str, object], expected: str) -> None:
    """The Study protocol cleanup (#353) must leave the Assay ``Output [URI]`` cell alone."""
    assay = InspireMapper().map_assay(_minimal_record(**overrides))

    output = next(col for col in assay.Tables[0].Columns if col.header.is_output)
    assert output.cells[0].AsFreeText == expected


def test_assay_has_no_output_uri_column_without_any_uri() -> None:
    assay = InspireMapper().map_assay(_minimal_record())

    assert not any(col.header.is_output for col in assay.Tables[0].Columns)


def test_record_without_uris_has_no_invented_dataset_uri_in_ro_crate() -> None:
    harvested = next(
        iter(
            InspireMapper().map(
                ParsedPayload(kind=PayloadKind.inspire_record, value=_minimal_record(), identifier="uuid-map-1"),
                MappingContext(source_url="https://csw.example.org/record/uuid-map-1"),
            )
        )
    )

    invented = [
        item["@id"]
        for item in json.loads(harvested.arc_json)["@graph"]
        if item.get("@type") == "URI" and str(item.get("@id", "")).endswith("_dataset")
    ]
    assert invented == []
