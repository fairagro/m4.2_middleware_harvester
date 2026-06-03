"""Schema.org mapper unit tests."""

import json

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.schema_org.schema_org_mapper import GeneralSchemaOrgMapper


def test_general_mapper_returns_jsonld() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))

    mapper = GeneralSchemaOrgMapper()
    result = mapper.map_graph(graph)

    assert result.startswith("{") and "@context" in result


def test_general_mapper_raises_when_no_dataset_entity_present() -> None:
    graph = Graph()

    mapper = GeneralSchemaOrgMapper()
    with pytest.raises(ValueError, match="Graph does not contain a Schema.org Dataset entity"):
        mapper.map_graph(graph)


def test_general_mapper_full_dataset_graph_includes_authors_and_comments() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("10.1234/abc")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))
    graph.add((dataset, schema.creator, Literal("Alice Example")))
    graph.add((dataset, schema.author, Literal("Alice Example")))
    graph.add((dataset, schema.contributor, Literal("Bob Contributor")))

    publisher = URIRef("https://example.org/publisher")
    graph.add((publisher, RDF.type, schema.Organization))
    graph.add((publisher, schema.name, Literal("Publisher Co")))
    graph.add((dataset, schema.publisher, publisher))

    graph.add((dataset, schema.keywords, Literal("science")))
    graph.add((dataset, schema.license, Literal("CC-BY")))
    graph.add((dataset, schema.inLanguage, Literal("en")))
    graph.add((dataset, schema.url, Literal("https://example.org/dataset/1")))
    graph.add((dataset, schema.conformsTo, Literal("https://example.org/spec")))
    graph.add((dataset, schema.citation, Literal("Citation text")))

    dist = BNode()
    graph.add((dataset, schema.distribution, dist))
    graph.add((dist, schema.encodingFormat, Literal("text/csv")))
    graph.add((dist, schema.contentUrl, Literal("https://example.org/data.csv")))

    mapper = GeneralSchemaOrgMapper()
    result = mapper.map_graph(graph)
    payload = json.loads(result)

    assert "@graph" in payload
    root = next(item for item in payload["@graph"] if item.get("@id") == "./")
    assert root["identifier"] == "10.1234/abc"
    assert "CC-BY" in result
    assert "Publisher Co" in result
