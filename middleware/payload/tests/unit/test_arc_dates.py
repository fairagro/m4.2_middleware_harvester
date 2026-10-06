"""Source dateModified on the RO-Crate root (#415)."""

from __future__ import annotations

import json

from arctrl import ARC, ArcInvestigation  # type: ignore[import-untyped]
from arctrl.py.Conversion.date_time import date_modified_key  # type: ignore[import-untyped]
from mapper_test_helpers import NO_DISCOVERY, first_harvest, parse_jsonld
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF

from middleware.payload.arc_dates import DATE_MODIFIED_COMMENT, date_modified_comment
from middleware.payload.inspire.mapper import InspireMapper
from middleware.payload.inspire.models import InspireRecord
from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.linked_data_mapper.regal_mapper import ORE, REGAL, RESEARCH_DATA_TYPE, RegalMapper


def _root(arc_json: str) -> dict[str, object]:
    return next(node for node in json.loads(arc_json)["@graph"] if node.get("@id") == "./")


def test_comment_name_is_arctrl_date_modified_key() -> None:
    """ARCtrl turns exactly this Comment name into the RO-Crate root dateModified."""
    assert date_modified_key == DATE_MODIFIED_COMMENT
    inv = ArcInvestigation.create(identifier="x", title="T")
    inv.Comments.append(date_modified_comment("Mon Jun 01 10:00:00 CEST 2020"))

    root = _root(ARC.from_arc_investigation(inv).ToROCrateJsonString())

    assert root["dateModified"] == "2020-06-01T10:00:00+02:00"


def test_not_a_date_gives_no_comment() -> None:
    assert date_modified_comment("last week") is None
    assert date_modified_comment(None) is None


def test_schema_org_date_modified_on_root() -> None:
    payload = json.dumps({
        "@context": "https://schema.org/",
        "@type": "Dataset",
        "@id": "https://example.org/ds/1",
        "name": "Modified dataset",
        "datePublished": "2011-01-01",
        "dateModified": "2019-03-04",
    })
    arc_json = first_harvest(GeneralSchemaOrgMapper().map_graph(parse_jsonld(payload), NO_DISCOVERY)).arc_json

    assert _root(arc_json)["dateModified"] == "2019-03-04"


def test_schema_org_without_date_modified_has_none() -> None:
    payload = json.dumps({
        "@context": "https://schema.org/",
        "@type": "Dataset",
        "@id": "https://example.org/ds/2",
        "name": "Plain",
    })
    arc_json = first_harvest(GeneralSchemaOrgMapper().map_graph(parse_jsonld(payload), NO_DISCOVERY)).arc_json

    assert "dateModified" not in _root(arc_json)


def _inspire_arc_json(dates: list[dict[str, str]]) -> str:
    record = InspireRecord.model_validate({
        "identifier": "uuid-dates",
        "title": "INSPIRE dates",
        "abstract": "Abstract",
        "date_stamp": "2026-08-18T12:06:54Z",
        "dates": dates,
    })
    return str(InspireMapper().map_record(record).ToROCrateJsonString())


def test_inspire_latest_revision_is_date_modified() -> None:
    arc_json = _inspire_arc_json([
        {"date": "2020-01-01", "datetype": "publication"},
        {"date": "2021-05-05", "datetype": "revision"},
        {"date": "2023-07-07", "datetype": "revision"},
    ])

    assert _root(arc_json)["dateModified"] == "2023-07-07"


def test_inspire_date_stamp_is_never_date_modified() -> None:
    """gmd:dateStamp is the metadata record's date (Metadata Date Comment), not the dataset's."""
    arc_json = _inspire_arc_json([{"date": "2020-01-01", "datetype": "publication"}])

    assert "dateModified" not in _root(arc_json)


def test_regal_described_by_modified_is_date_modified() -> None:
    subject = URIRef("https://example.org/resource/frl:1")
    described_by = URIRef("https://example.org/resource/frl:1.rdf")
    graph = Graph()
    graph.add((subject, RDF.type, RESEARCH_DATA_TYPE))
    graph.add((subject, DCTERMS.title, Literal("Regal dates")))
    graph.add((subject, REGAL.doi, Literal("10.4126/FRL01-1")))
    graph.add((subject, ORE.isDescribedBy, described_by))
    graph.add((described_by, DCTERMS.modified, Literal("2024-09-04T09:34:30.938+0200")))

    mapper = RegalMapper(resource_base_url="https://example.org/resource/")
    arc_json = first_harvest(mapper.map_graph(graph, NO_DISCOVERY)).arc_json

    assert _root(arc_json)["dateModified"] == "2024-09-04T09:34:30.938+0200"
