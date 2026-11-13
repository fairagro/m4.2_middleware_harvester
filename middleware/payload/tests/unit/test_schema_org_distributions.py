"""Schema.org mapper: DataDownload distributions, protocols, landing page."""

from __future__ import annotations

import pytest
from mapper_test_helpers import (
    NO_DISCOVERY,
    OPENAGRAR_PROPERTYVALUE_DOI,
    assay_output_uri,
    assert_harvest_has_no_bnode_labels,
    comment_text,
    distribution_comment_texts,
    first_harvest,
    invented_data_entities,
    parse_jsonld,
    processing_parameters,
)
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.placeholders import PlaceholderConfig


def test_distribution_comments_stable_across_bnode_order() -> None:
    schema = Namespace("https://schema.org/")

    def build(order: list[tuple[str, str]]) -> Graph:
        graph = Graph()
        dataset = URIRef("https://example.org/dist-order")
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("Distribution Order Dataset")))
        graph.add((dataset, schema.identifier, Literal("10.9/dist-order")))
        for encoding, url in order:
            dist = BNode()
            graph.add((dataset, schema.distribution, dist))
            graph.add((dist, schema.encodingFormat, Literal(encoding)))
            graph.add((dist, schema.contentUrl, Literal(url)))
        return graph

    order_a = [
        ("text/csv", "https://example.org/a.csv"),
        ("application/json", "https://example.org/b.json"),
    ]
    order_b = list(reversed(order_a))
    first = distribution_comment_texts(
        first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(build(order_a), NO_DISCOVERY)).arc_json
    )
    second = distribution_comment_texts(
        first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(build(order_b), NO_DISCOVERY)).arc_json
    )
    assert first == second
    assert set(first) == {
        "text/csv: https://example.org/a.csv",
        "application/json: https://example.org/b.json",
    }


def test_single_datadownload_creates_distribution_comment() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/dataset/dist-1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Single Distribution Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/dist-1")))

    dist = BNode()
    graph.add((dataset, schema.distribution, dist))
    graph.add((dist, schema.encodingFormat, Literal("text/csv")))
    graph.add((dist, schema.contentUrl, Literal("https://repo.example.org/data/file.csv")))

    arc_json = first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY)).arc_json
    assert_harvest_has_no_bnode_labels(arc_json)
    texts = distribution_comment_texts(arc_json)
    assert texts == ["text/csv: https://repo.example.org/data/file.csv"]


def test_multiple_datadownload_creates_multiple_distribution_comments() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/dataset/dist-multi")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Multi Distribution Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/dist-multi")))

    dist1 = BNode()
    graph.add((dataset, schema.distribution, dist1))
    graph.add((dist1, schema.encodingFormat, Literal("text/csv")))
    graph.add((dist1, schema.contentUrl, Literal("https://repo.example.org/data.csv")))

    dist2 = BNode()
    graph.add((dataset, schema.distribution, dist2))
    graph.add((dist2, schema.encodingFormat, Literal("application/json")))
    graph.add((dist2, schema.contentUrl, Literal("https://repo.example.org/data.json")))

    arc_json = first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY)).arc_json
    assert_harvest_has_no_bnode_labels(arc_json)
    texts = distribution_comment_texts(arc_json)
    assert set(texts) == {
        "text/csv: https://repo.example.org/data.csv",
        "application/json: https://repo.example.org/data.json",
    }


def test_datadownload_without_encoding_format_skips_format_comment() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/dataset/dist-noenc")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("No Encoding Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/dist-noenc")))

    dist = BNode()
    graph.add((dataset, schema.distribution, dist))
    graph.add((dist, schema.contentUrl, Literal("https://repo.example.org/data.bin")))

    arc_json = first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY)).arc_json
    assert_harvest_has_no_bnode_labels(arc_json)
    texts = distribution_comment_texts(arc_json)
    assert texts == ["https://repo.example.org/data.bin"]


def test_datadownload_distribution_comments_deterministic_order() -> None:
    schema = Namespace("https://schema.org/")

    def build(order: list[tuple[str, str]]) -> Graph:
        graph = Graph()
        dataset = URIRef("https://example.org/dist-deterministic")
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("Deterministic Distribution Dataset")))
        graph.add((dataset, schema.identifier, Literal("10.9/dist-deterministic")))
        for encoding, url in order:
            dist = BNode()
            graph.add((dataset, schema.distribution, dist))
            graph.add((dist, schema.encodingFormat, Literal(encoding)))
            graph.add((dist, schema.contentUrl, Literal(url)))
        return graph

    order_a = [
        ("text/csv", "https://example.org/a.csv"),
        ("application/json", "https://example.org/b.json"),
    ]
    order_b = list(reversed(order_a))
    first = distribution_comment_texts(
        first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(build(order_a), NO_DISCOVERY)).arc_json
    )
    second = distribution_comment_texts(
        first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(build(order_b), NO_DISCOVERY)).arc_json
    )
    assert first == second
    assert set(first) == {
        "text/csv: https://example.org/a.csv",
        "application/json: https://example.org/b.json",
    }


# --- no invented data files (#353) ------------------------------------------


def test_data_processing_does_not_invent_data_files_in_ro_crate() -> None:
    harvested = first_harvest(
        GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(parse_jsonld(OPENAGRAR_PROPERTYVALUE_DOI), NO_DISCOVERY)
    )

    assert invented_data_entities(harvested.arc_json) == []


def test_data_processing_keeps_its_parameters() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("10.1234/abc")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))
    publisher = URIRef("https://example.org/publisher")
    graph.add((publisher, RDF.type, schema.Organization))
    graph.add((publisher, schema.name, Literal("Publisher Co")))
    graph.add((dataset, schema.publisher, publisher))

    harvested = first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY))

    assert processing_parameters(harvested.arc_json, "Data Processing") == {
        "Processing Description": (
            "Data processing and publication according to Schema.org metadata standard | Publisher: Publisher Co"
        )
    }


def test_assay_output_uri_is_unchanged() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))

    harvested = first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY))

    assert assay_output_uri(harvested.arc_json) == "https://example.org/dataset/1"


# --- landing page comment (#534) --------------------------------------------


def test_schema_url_becomes_landing_page_comment() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))
    graph.add((dataset, schema.url, Literal("https://repo.example.org/dataset/abc")))

    harvested = first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY))

    assert comment_text(harvested.arc_json, "Landing Page") == "https://repo.example.org/dataset/abc"


def test_url_comment_is_kept_alongside_landing_page() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))
    graph.add((dataset, schema.url, Literal("https://repo.example.org/dataset/abc")))

    harvested = first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY))

    assert comment_text(harvested.arc_json, "URL") == "https://repo.example.org/dataset/abc"


@pytest.mark.parametrize("url", [None, "n/a"])
def test_no_landing_page_comment_without_usable_schema_url(url: str | None) -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))
    if url is not None:
        graph.add((dataset, schema.url, Literal(url)))

    mapper = GeneralSchemaOrgMapper(PlaceholderConfig(values=frozenset({"n/a"})))
    harvested = first_harvest(mapper.map_graph(graph, NO_DISCOVERY))

    assert comment_text(harvested.arc_json, "Landing Page") is None


def test_assay_does_not_invent_dataset_source_input() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/no-source")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("No Source Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/no-source")))

    harvested = first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY))

    assert "Source_Dataset_Source" not in harvested.arc_json
