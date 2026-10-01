"""Unit tests for InspireMapper DataMapper.map harvest path."""

from __future__ import annotations

import pytest

from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.inspire.mapper import InspireMapper
from middleware.payload.inspire.models import InspireRecord
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
