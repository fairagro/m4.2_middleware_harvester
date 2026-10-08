"""RDI placeholder values (#413)."""

from __future__ import annotations

import pytest
from mapper_test_helpers import NO_DISCOVERY, first_harvest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF

from middleware.payload.linked_data_mapper.ckanext_dcat_mapper import CkanextDcatMapper
from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.linked_data_mapper.regal_mapper import REGAL, RESEARCH_DATA_TYPE, RegalMapper
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.placeholders import PlaceholderConfig

SCHEMA = Namespace("https://schema.org/")

GEONODE = PlaceholderConfig(values=frozenset({"None", "No information provided", "N/A"}))
TEMPLATES = PlaceholderConfig(unrendered_templates=True)


@pytest.mark.parametrize(
    ("placeholders", "value"),
    [
        (GEONODE, "None"),
        (GEONODE, "  none "),
        (GEONODE, "n/a"),
        (GEONODE, "No information provided"),
        (TEMPLATES, "$licenseURL"),
        (TEMPLATES, "${licenseURL}"),
        (TEMPLATES, "{{ license_url }}"),
    ],
)
def test_matches(placeholders: PlaceholderConfig, value: str) -> None:
    assert placeholders.matches(value)


@pytest.mark.parametrize(
    ("placeholders", "value"),
    [
        (GEONODE, ""),
        (GEONODE, "None of the plots were irrigated."),
        (GEONODE, "Not Specified: The original author did not specify a license."),
        (GEONODE, "$licenseURL"),
        (TEMPLATES, "None"),
        (TEMPLATES, "$5"),
    ],
)
def test_does_not_match(placeholders: PlaceholderConfig, value: str) -> None:
    assert not placeholders.matches(value)


def test_nothing_matches_by_default() -> None:
    """Defaults live in the model and are empty: only what the operator configures is dropped."""
    placeholders = MapperConfig(type=MapperType.schema_org_general).placeholders

    assert placeholders == PlaceholderConfig()
    assert not any(placeholders.matches(v) for v in ("None", "null", "N/A", "$licenseURL", "{{x}}"))


def test_configured_values_are_folded() -> None:
    config = MapperConfig.model_validate({
        "type": "schema_org_general",
        "placeholders": {"values": [" Keine Angabe ", ""], "unrendered_templates": True},
    })

    assert config.placeholders.values == frozenset({"keine angabe"})
    assert config.placeholders.unrendered_templates
    assert config.placeholders.matches("KEINE ANGABE")
    assert not config.placeholders.matches("None")


def _schema_org_graph(license_text: str) -> Graph:
    graph = Graph()
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, SCHEMA.Dataset))
    graph.add((dataset, SCHEMA.name, Literal("Placeholder dataset")))
    graph.add((dataset, SCHEMA.license, Literal(license_text)))
    graph.add((dataset, SCHEMA.version, Literal("None")))
    return graph


def test_schema_org_mapper_uses_repository_placeholders() -> None:
    config = MapperConfig.model_validate({"type": "schema_org_general", "placeholders": {"values": ["Lizenz folgt"]}})
    mapper = GeneralSchemaOrgMapper.from_config(config)

    arc_json = first_harvest(mapper.map_graph(_schema_org_graph("Lizenz folgt"), NO_DISCOVERY)).arc_json

    assert "Lizenz folgt" not in arc_json
    # Only the configured value is dropped; "None" is not configured for this RDI.
    assert '"None"' in arc_json


def test_regal_mapper_uses_repository_placeholders() -> None:
    config = MapperConfig.model_validate({
        "type": "regal_general",
        "resource_base_url": "https://example.org/resource/",
        "placeholders": {"values": ["Lizenz folgt"]},
    })
    subject = URIRef("https://example.org/resource/frl:1")
    graph = Graph()
    graph.add((subject, RDF.type, RESEARCH_DATA_TYPE))
    graph.add((subject, DCTERMS.title, Literal("Regal placeholders")))
    graph.add((subject, REGAL.doi, Literal("10.4126/FRL01-1")))
    graph.add((subject, REGAL.license, Literal("Lizenz folgt")))

    arc_json = first_harvest(RegalMapper.from_config(config).map_graph(graph, NO_DISCOVERY)).arc_json

    assert "ALL RIGHTS RESERVED BY THE AUTHORS" in arc_json


def test_linked_data_mapper_license_applies_placeholders() -> None:
    """``LinkedDataMapper.license`` is ``license_from_value`` with the mapper's placeholders (#459)."""
    config = MapperConfig.model_validate({"type": "schema_org_general", "placeholders": {"unrendered_templates": True}})
    mapper = GeneralSchemaOrgMapper.from_config(config)

    assert mapper.placeholders is config.placeholders
    assert mapper.license("$licenseURL") is None
    assert mapper.license("CC-BY-4.0") is not None


def test_ckanext_dcat_mapper_takes_repository_placeholders() -> None:
    config = MapperConfig.model_validate({"type": "ckanext_dcat", "placeholders": {"values": ["n/a"]}})
    mapper = CkanextDcatMapper.from_config(config)

    assert mapper.placeholders is config.placeholders
