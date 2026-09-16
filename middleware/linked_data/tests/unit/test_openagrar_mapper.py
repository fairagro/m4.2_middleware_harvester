"""OpenAgrar Schema.org mapper overlay unit tests (issue #164, issue #227)."""

import logging
from concurrent.futures import ThreadPoolExecutor

import pytest
from mapper_test_helpers import (
    NO_DISCOVERY,
    OPENAGRAR_MISSING_NAME_NO_FALLBACK,
    OPENAGRAR_MISSING_NAME_WITH_ALTERNATIVE_HEADLINE,
    OPENAGRAR_MISSING_NAME_WITH_HEADLINE,
    OPENAGRAR_PROPERTYVALUE_DOI,
    first_harvest,
    parse_jsonld,
    root_identifier,
    root_title,
    title_source_comment_text,
)
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.harvester.plugin_base import HarvestedArc
from middleware.linked_data.linked_data_mapper import GeneralSchemaOrgMapper, MappingContext
from middleware.linked_data.linked_data_mapper.openagrar_schema_org_mapper import OpenAgrarSchemaOrgMapper


def test_headline_fallback_used_when_name_missing(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        harvested = first_harvest(
            OpenAgrarSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_MISSING_NAME_WITH_HEADLINE), NO_DISCOVERY)
        )
    assert root_title(harvested.arc_json) == "Flower visitors in legume-intercrops"
    assert title_source_comment_text(harvested.arc_json) == "headline"
    assert any("headline" in record.message for record in caplog.records)
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_alternative_headline_first_non_empty_used() -> None:
    harvested = first_harvest(
        OpenAgrarSchemaOrgMapper().map_graph(
            parse_jsonld(OPENAGRAR_MISSING_NAME_WITH_ALTERNATIVE_HEADLINE), NO_DISCOVERY
        )
    )
    assert root_title(harvested.arc_json) == "Flower visitors in legume-intercrops"
    assert title_source_comment_text(harvested.arc_json) == "alternativeHeadline"


def test_html_title_fallback_used_when_context_supplies_it() -> None:
    context = MappingContext(html_title="Citation Title From Page")
    harvested = first_harvest(
        OpenAgrarSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_MISSING_NAME_NO_FALLBACK), context)
    )
    assert root_title(harvested.arc_json) == "Citation Title From Page"
    assert title_source_comment_text(harvested.arc_json) == "html_title"


def test_no_fallback_available_fails_closed_naming_all_four_carriers() -> None:
    with pytest.raises(
        ValueError,
        match=r"no usable title \(schema:name, headline, alternativeHeadline, html_title\)",
    ):
        list(OpenAgrarSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_MISSING_NAME_NO_FALLBACK), NO_DISCOVERY))


def test_schema_name_present_matches_base_mapper_identifier_and_title() -> None:
    """Overlay parity: schema:name present yields identical results to the base mapper."""
    graph = parse_jsonld(OPENAGRAR_PROPERTYVALUE_DOI)

    base_harvested = first_harvest(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY))
    overlay_harvested = first_harvest(OpenAgrarSchemaOrgMapper().map_graph(graph, NO_DISCOVERY))

    assert root_identifier(overlay_harvested.arc_json) == root_identifier(base_harvested.arc_json)
    assert root_title(overlay_harvested.arc_json) == root_title(base_harvested.arc_json)
    assert title_source_comment_text(overlay_harvested.arc_json) is None


def test_concurrent_map_graph_on_shared_overlay_mapper_does_not_cross_talk() -> None:
    """One overlay mapper + worker threads must not mix StableGraph sessions (plugin shape)."""
    schema = Namespace("https://schema.org/")

    def build(slug: str, title: str) -> Graph:
        graph = Graph()
        dataset = URIRef(f"https://example.org/dataset/{slug}")
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal(title)))
        graph.add((dataset, schema.url, dataset))
        return graph

    mapper = OpenAgrarSchemaOrgMapper()
    left = build("alpha", "Alpha Title")
    right = build("zeta", "Zeta Title")

    def map_in_worker(graph: Graph) -> list[HarvestedArc]:
        return list(mapper.map_graph(graph, NO_DISCOVERY))

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(map_in_worker, left),
            pool.submit(map_in_worker, right),
        ]
        results = [item for future in futures for item in future.result()]

    by_id = {root_identifier(harvested.arc_json): harvested.arc_json for harvested in results}
    assert set(by_id) == {"example_org_dataset_alpha", "example_org_dataset_zeta"}
    assert "Alpha Title" in by_id["example_org_dataset_alpha"]
    assert "Zeta Title" not in by_id["example_org_dataset_alpha"]
