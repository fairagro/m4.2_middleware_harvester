"""Unit tests for shared ``arc_license.license_from_value`` and Schema.org / Regal use."""

from __future__ import annotations

import json

import pytest
from mapper_test_helpers import NO_DISCOVERY, first_harvest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF

from middleware.payload.arc_license import license_from_value
from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.linked_data_mapper.regal_mapper import REGAL, RESEARCH_DATA_TYPE, RegalMapper
from middleware.payload.placeholders import PlaceholderConfig

SCHEMA = Namespace("https://schema.org/")
CC_BY = "https://creativecommons.org/licenses/by/4.0/"
ARCTRL_DEFAULT = "ALL RIGHTS RESERVED BY THE AUTHORS"

# e!DAL renders an unexpanded ``$licenseURL`` (#413); the repository opts into template matching.
EDAL_PLACEHOLDERS = PlaceholderConfig(unrendered_templates=True)


def _license_text(arc_json: str) -> str | None:
    """Text of the RO-Crate licence node the root dataset points to."""
    graph = json.loads(arc_json)["@graph"]
    root = next(node for node in graph if node.get("@id") == "./")
    license_id = root["license"]["@id"]
    node = next(node for node in graph if node.get("@id") == license_id)
    text = node.get("text")
    return str(text) if text is not None else None


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
    license_ = license_from_value(value, name=name, placeholders=PlaceholderConfig())
    assert license_ is not None
    assert license_.Content == expected
    assert license_.Path == "LICENSE"


@pytest.mark.parametrize("value", [None, "", "   ", "$licenseURL", "${licenseURL}"])
def test_license_from_value_rejects_empty_and_placeholders(value: str | None) -> None:
    assert license_from_value(value, placeholders=EDAL_PLACEHOLDERS) is None


def test_license_from_value_keeps_template_unless_configured() -> None:
    license_ = license_from_value("$licenseURL", placeholders=PlaceholderConfig())
    assert license_ is not None
    assert license_.Content == "$licenseURL"


def _schema_org_graph(license_obj: Literal | URIRef | BNode | None) -> Graph:
    graph = Graph()
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, SCHEMA.Dataset))
    graph.add((dataset, SCHEMA.name, Literal("Licensed dataset")))
    if license_obj is not None:
        graph.add((dataset, SCHEMA.license, license_obj))
    return graph


def test_schema_org_mapper_sets_url_licence() -> None:
    arc_json = first_harvest(
        GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(_schema_org_graph(URIRef(CC_BY)), NO_DISCOVERY)
    )
    assert _license_text(arc_json.arc_json) == CC_BY


def test_schema_org_mapper_creative_work_licence_uses_url_and_name() -> None:
    graph = _schema_org_graph(None)
    work = BNode()
    graph.add((URIRef("https://example.org/dataset/1"), SCHEMA.license, work))
    graph.add((work, RDF.type, SCHEMA.CreativeWork))
    graph.add((work, SCHEMA.name, Literal("CC BY 4.0")))
    graph.add((work, SCHEMA.url, URIRef(CC_BY)))
    arc_json = first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY)).arc_json
    assert _license_text(arc_json) == f"CC BY 4.0 ({CC_BY})"


@pytest.mark.parametrize("license_obj", [None, Literal("$licenseURL")])
def test_schema_org_mapper_keeps_arctrl_default_without_licence(license_obj: Literal | None) -> None:
    mapper = GeneralSchemaOrgMapper(EDAL_PLACEHOLDERS)
    arc_json = first_harvest(mapper.map_graph(_schema_org_graph(license_obj), NO_DISCOVERY))
    assert _license_text(arc_json.arc_json) == ARCTRL_DEFAULT


def test_schema_org_mapper_writes_no_license_comment_for_placeholder() -> None:
    """e!DAL renders an unexpanded ``$licenseURL`` (#413); it must not become a License comment."""
    arc_json = first_harvest(
        GeneralSchemaOrgMapper(EDAL_PLACEHOLDERS).map_graph(_schema_org_graph(Literal("$licenseURL")), NO_DISCOVERY)
    ).arc_json
    assert "$licenseURL" not in arc_json


def test_regal_mapper_sets_licence() -> None:
    subject = URIRef("https://example.org/resource/frl:1")
    graph = Graph()
    graph.add((subject, RDF.type, RESEARCH_DATA_TYPE))
    graph.add((subject, DCTERMS.title, Literal("Regal licence")))
    graph.add((subject, REGAL.doi, Literal("10.4126/FRL01-1")))
    graph.add((subject, REGAL.license, URIRef("http://opendatacommons.org/licenses/by/1.0/")))
    mapper = RegalMapper("https://example.org/resource/", PlaceholderConfig())
    arc_json = first_harvest(mapper.map_graph(graph, NO_DISCOVERY)).arc_json
    assert _license_text(arc_json) == "http://opendatacommons.org/licenses/by/1.0/"
