"""RDI placeholder values (#413)."""

from __future__ import annotations

import pytest
from mapper_test_helpers import NO_DISCOVERY, first_harvest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF

from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.linked_data_mapper.regal_mapper import REGAL, RESEARCH_DATA_TYPE, RegalMapper
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.placeholders import DEFAULT_PLACEHOLDER_VALUES, is_placeholder, normalize_placeholder_values

SCHEMA = Namespace("https://schema.org/")


@pytest.mark.parametrize(
    "value",
    [
        "None",
        "  none ",
        "NULL",
        "n/a",
        "No abstract provided",
        "Keine Zusammenfassung vorhanden",
        "No information provided",
        "$licenseURL",
        "${licenseURL}",
        "{{ license_url }}",
    ],
)
def test_is_placeholder(value: str) -> None:
    assert is_placeholder(value)


@pytest.mark.parametrize(
    "value",
    ["", "None of the plots were irrigated.", "Not Specified: The original author did not specify a license.", "$5"],
)
def test_is_not_placeholder(value: str) -> None:
    assert not is_placeholder(value)


def test_custom_values_are_folded() -> None:
    values = normalize_placeholder_values([" Keine Angabe ", ""])

    assert values == frozenset({"keine angabe"})
    assert is_placeholder("KEINE ANGABE", values)
    assert not is_placeholder("None", values)


def test_mapper_config_placeholders_default_and_per_rdi() -> None:
    assert MapperConfig(type=MapperType.schema_org_general).placeholder_values == DEFAULT_PLACEHOLDER_VALUES
    custom = MapperConfig.model_validate({"type": "schema_org_general", "placeholder_values": [" Keine Angabe ", "$x"]})
    assert custom.placeholder_values == frozenset({"keine angabe", "$x"})


def _schema_org_graph(license_text: str) -> Graph:
    graph = Graph()
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, SCHEMA.Dataset))
    graph.add((dataset, SCHEMA.name, Literal("Placeholder dataset")))
    graph.add((dataset, SCHEMA.license, Literal(license_text)))
    graph.add((dataset, SCHEMA.version, Literal("None")))
    return graph


def test_schema_org_mapper_uses_repository_placeholders() -> None:
    config = MapperConfig.model_validate({"type": "schema_org_general", "placeholder_values": ["Lizenz folgt"]})
    mapper = GeneralSchemaOrgMapper.from_config(config)

    arc_json = first_harvest(mapper.map_graph(_schema_org_graph("Lizenz folgt"), NO_DISCOVERY)).arc_json

    assert "Lizenz folgt" not in arc_json
    # The per-RDI list replaced the defaults, so "None" is kept for this RDI.
    assert '"None"' in arc_json


def test_regal_mapper_uses_repository_placeholders() -> None:
    config = MapperConfig.model_validate({
        "type": "regal_general",
        "resource_base_url": "https://example.org/resource/",
        "placeholder_values": ["Lizenz folgt"],
    })
    subject = URIRef("https://example.org/resource/frl:1")
    graph = Graph()
    graph.add((subject, RDF.type, RESEARCH_DATA_TYPE))
    graph.add((subject, DCTERMS.title, Literal("Regal placeholders")))
    graph.add((subject, REGAL.doi, Literal("10.4126/FRL01-1")))
    graph.add((subject, REGAL.license, Literal("Lizenz folgt")))

    arc_json = first_harvest(RegalMapper.from_config(config).map_graph(graph, NO_DISCOVERY)).arc_json

    assert "ALL RIGHTS RESERVED BY THE AUTHORS" in arc_json
