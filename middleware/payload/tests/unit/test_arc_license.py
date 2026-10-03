"""Unit tests for the ARC licence helpers and their use in the Schema.org, Regal and INSPIRE mappers."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from arctrl import ARC  # type: ignore[import-untyped]
from mapper_test_helpers import NO_DISCOVERY, first_harvest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF

from middleware.payload.arc_license import inspire_license, license_from_value
from middleware.payload.inspire.mapper import InspireMapper
from middleware.payload.inspire.models import InspireRecord
from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.linked_data_mapper.regal_mapper import REGAL, RESEARCH_DATA_TYPE, RegalMapper

SCHEMA = Namespace("https://schema.org/")
CC_BY = "https://creativecommons.org/licenses/by/4.0/"
ARCTRL_DEFAULT = "ALL RIGHTS RESERVED BY THE AUTHORS"

BONARES_CC_BY = (
    "CC-BY (CC-BY): https://creativecommons.org/licenses/by/4.0/ "
    "(https://creativecommons.org/licenses/by/4.0/legalcode)"
)
THUENEN_DL_DE = (
    "Data licence Germany – attribution – version 2.0 (dl-de/by-2-0): Data licence Germany – attribution – "
    "version 2.0. See info at: https://www.govdata.de/dl-de/by-2-0 (http://www.govdata.de/dl-de/by-2-0)"
)
NOT_SPECIFIED = "Not Specified: The original author did not specify a license."


def _license_text(arc_json: str) -> str | None:
    """Text of the RO-Crate licence node the root dataset points to."""
    graph = json.loads(arc_json)["@graph"]
    root = next(node for node in graph if node.get("@id") == "./")
    license_id = root["license"]["@id"]
    node = next(node for node in graph if node.get("@id") == license_id)
    text = node.get("text")
    return str(text) if text is not None else None


# --- license_from_value -----------------------------------------------------


@pytest.mark.parametrize(
    ("value", "name", "expected"),
    [
        (CC_BY, None, CC_BY),
        (f"  {CC_BY} ", None, CC_BY),
        (CC_BY, "CC BY 4.0", f"CC BY 4.0 ({CC_BY})"),
        (CC_BY, CC_BY, CC_BY),
        ("CC-BY", None, "CC-BY"),
        ("CC-BY", "ignored for text", "CC-BY"),
    ],
)
def test_license_from_value_keeps_url_or_text(value: str, name: str | None, expected: str) -> None:
    license_ = license_from_value(value, name=name)
    assert license_ is not None
    assert license_.Content == expected
    assert license_.Path == "LICENSE"


@pytest.mark.parametrize("value", [None, "", "   ", "$licenseURL", "${licenseURL}"])
def test_license_from_value_rejects_empty_and_placeholders(value: str | None) -> None:
    assert license_from_value(value) is None


# --- inspire_license --------------------------------------------------------


@pytest.mark.parametrize(
    "constraints",
    [
        [BONARES_CC_BY, "Disclaimer Author (en) These data were created …"],
        [THUENEN_DL_DE],
        ["None", "GeoNutzV (GeoNutzV): Verordnung … (http://www.gesetze-im-internet.de/geonutzv/)"],
    ],
)
def test_inspire_license_takes_first_geonode_licence_text(constraints: list[str]) -> None:
    license_ = inspire_license(constraints, [])
    expected = next(c for c in constraints if " (" in c and "):" in c)
    assert license_ is not None
    assert license_.Content == expected
    assert license_.Path == "LICENSE"


def test_inspire_license_prefers_non_registry_anchor_url() -> None:
    license_ = inspire_license(
        ["Datenlizenz Deutschland – Namensnennung – Version 2.0"],
        [
            "http://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply",
            "https://www.govdata.de/dl-de/by-2-0",
        ],
    )
    assert license_ is not None
    assert license_.Content == "https://www.govdata.de/dl-de/by-2-0"


def test_inspire_license_free_text_with_licence_host_url() -> None:
    text = "Nutzung gemäß https://creativecommons.org/licenses/by/4.0/ mit Quellenangabe"
    license_ = inspire_license(["keine", text], [])
    assert license_ is not None
    assert license_.Content == text


@pytest.mark.parametrize(
    "constraints",
    [
        [],
        [NOT_SPECIFIED],
        [f"{NOT_SPECIFIED}", "None"],
        [NOT_SPECIFIED, "see https://creativecommons.org/licenses/by/4.0/"],
        ["Access for data download upon request to someone@example.org."],
        ["Data are available on request.", "keine", "See info at https://www.example.org/terms"],
    ],
)
def test_inspire_license_none_without_licence(constraints: list[str]) -> None:
    assert inspire_license(constraints, ["", ""]) is None


# --- mappers ----------------------------------------------------------------


def _schema_org_graph(license_obj: Literal | URIRef | BNode | None) -> Graph:
    graph = Graph()
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, SCHEMA.Dataset))
    graph.add((dataset, SCHEMA.name, Literal("Licensed dataset")))
    if license_obj is not None:
        graph.add((dataset, SCHEMA.license, license_obj))
    return graph


def test_schema_org_mapper_sets_url_licence() -> None:
    arc_json = first_harvest(GeneralSchemaOrgMapper().map_graph(_schema_org_graph(URIRef(CC_BY)), NO_DISCOVERY))
    assert _license_text(arc_json.arc_json) == CC_BY


def test_schema_org_mapper_creative_work_licence_uses_url_and_name() -> None:
    graph = _schema_org_graph(None)
    work = BNode()
    graph.add((URIRef("https://example.org/dataset/1"), SCHEMA.license, work))
    graph.add((work, RDF.type, SCHEMA.CreativeWork))
    graph.add((work, SCHEMA.name, Literal("CC BY 4.0")))
    graph.add((work, SCHEMA.url, URIRef(CC_BY)))
    arc_json = first_harvest(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY)).arc_json
    assert _license_text(arc_json) == f"CC BY 4.0 ({CC_BY})"


@pytest.mark.parametrize("license_obj", [None, Literal("$licenseURL")])
def test_schema_org_mapper_keeps_arctrl_default_without_licence(license_obj: Literal | None) -> None:
    arc_json = first_harvest(GeneralSchemaOrgMapper().map_graph(_schema_org_graph(license_obj), NO_DISCOVERY))
    assert _license_text(arc_json.arc_json) == ARCTRL_DEFAULT


def test_regal_mapper_sets_licence() -> None:
    subject = URIRef("https://example.org/resource/frl:1")
    graph = Graph()
    graph.add((subject, RDF.type, RESEARCH_DATA_TYPE))
    graph.add((subject, DCTERMS.title, Literal("Regal licence")))
    graph.add((subject, REGAL.doi, Literal("10.4126/FRL01-1")))
    graph.add((subject, REGAL.license, URIRef("http://opendatacommons.org/licenses/by/1.0/")))
    mapper = RegalMapper(resource_base_url="https://example.org/resource/")
    arc_json = first_harvest(mapper.map_graph(graph, NO_DISCOVERY)).arc_json
    assert _license_text(arc_json) == "http://opendatacommons.org/licenses/by/1.0/"


def _inspire_record(other_constraints: list[str]) -> InspireRecord:
    return InspireRecord.model_validate({
        "identifier": "uuid-licence",
        "title": "INSPIRE licence",
        "abstract": "Abstract",
        "other_constraints": other_constraints,
    })


@pytest.mark.parametrize(
    ("constraints", "expected"),
    [([BONARES_CC_BY], BONARES_CC_BY), ([NOT_SPECIFIED], ARCTRL_DEFAULT)],
)
def test_inspire_mapper_sets_licence(constraints: list[str], expected: str) -> None:
    arc = InspireMapper().map_record(_inspire_record(constraints))
    assert _license_text(arc.ToROCrateJsonString()) == expected


def test_licence_round_trips_through_arc_write_without_url_paths(tmp_path: Path) -> None:
    """The API rebuilds ARCs from these RO-Crates and writes them; the licence must stay a file."""
    arc_json = InspireMapper().map_record(_inspire_record([BONARES_CC_BY])).ToROCrateJsonString()
    arc = ARC.from_rocrate_json_string(arc_json)
    assert arc.License.Content == BONARES_CC_BY

    arc.Write(str(tmp_path))

    assert (tmp_path / "LICENSE").read_text(encoding="utf-8") == BONARES_CC_BY
    for _root, dirnames, _files in os.walk(tmp_path):
        assert not [d for d in dirnames if d.startswith("http")]
