"""Schema.org mapper unit tests."""

from rdflib import Graph, Literal, Namespace, URIRef
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
