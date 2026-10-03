"""Unit tests for InspireMapper DataMapper.map harvest path."""

from __future__ import annotations

import json

import pytest

from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.inspire.mapper import InspireMapper
from middleware.payload.inspire.models import Contact, InspireRecord, ResourceIdentifier
from middleware.payload.kinds import PayloadKind
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

    assert arc.SubmissionDate == "2026-05-19T09:13:00Z"
    assert arc.Studies[0].SubmissionDate == "2026-05-19T09:13:00Z"
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
def test_dataset_date_order_publication_revision_creation(
    dates: list[tuple[str, str | None]], expected: str | None
) -> None:
    record = _minimal_record(
        date_stamp="2026-08-18",
        dates=[{"date": date, "datetype": datetype} for date, datetype in dates],
    )
    arc = InspireMapper().map_record(record)
    assert (arc.SubmissionDate or None) == expected
