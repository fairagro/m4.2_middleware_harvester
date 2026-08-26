"""Unit tests for StableGraph / ResourceView."""

from __future__ import annotations

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.linked_data.linked_data_mapper.stable_graph import SCHEMA_ORG_NAMESPACES, StableGraph

SCHEMA = Namespace("https://schema.org/")
SCHEMA_HTTP = Namespace("http://schema.org/")


def _wrap(graph: Graph) -> StableGraph:
    return StableGraph.wrap(
        graph,
        term_namespaces=SCHEMA_ORG_NAMESPACES,
        label_predicates=tuple(ns.name for ns in SCHEMA_ORG_NAMESPACES),
    )


def test_blank_node_subject_has_no_iri() -> None:
    graph = Graph()
    subject = BNode()
    graph.add((subject, RDF.type, SCHEMA.Dataset))
    view = _wrap(graph).view(subject)
    assert view.iri is None


def test_literal_prefers_english_over_de_and_empty() -> None:
    graph = Graph()
    subject = URIRef("https://example.org/ds")
    graph.add((subject, SCHEMA.description, Literal("")))
    graph.add((subject, SCHEMA.description, Literal("Deutsch", lang="de")))
    graph.add((subject, SCHEMA.description, Literal("English", lang="en")))
    text = _wrap(graph).view(subject).literal(SCHEMA.description)
    assert text is not None
    assert text.value == "English"


def test_literals_order_stable_under_permutation() -> None:
    def build(order: list[str]) -> list[str]:
        graph = Graph()
        subject = URIRef("https://example.org/kw")
        for word in order:
            graph.add((subject, SCHEMA.keywords, Literal(word)))
        return [t.value for t in _wrap(graph).view(subject).literals(SCHEMA.keywords)]

    assert build(["zeta", "alpha", "Beta"]) == build(["Beta", "zeta", "alpha"])
    assert build(["zeta", "alpha", "Beta"]) == ["alpha", "Beta", "zeta"]


def test_resources_rank_bnodes_by_content_not_label() -> None:
    def build(names: list[str]) -> str:
        graph = Graph()
        dataset = URIRef("https://example.org/pub")
        for label in names:
            publisher = BNode()
            graph.add((dataset, SCHEMA.publisher, publisher))
            graph.add((publisher, SCHEMA.name, Literal(label)))
        view = _wrap(graph).view(dataset).resource(SCHEMA.publisher)
        assert view is not None
        text = view.text(SCHEMA.name)
        assert text is not None
        return text

    assert build(["Zeta Org", "Alpha Org"]) == build(["Alpha Org", "Zeta Org"])
    assert build(["Zeta Org", "Alpha Org"]) == "Alpha Org"


def test_labelled_skips_unlabelled_bnode() -> None:
    graph = Graph()
    subject = URIRef("https://example.org/ds")
    graph.add((subject, SCHEMA.keywords, BNode()))
    graph.add((subject, SCHEMA.keywords, Literal("kept")))
    labelled = _wrap(graph).view(subject).labelled(SCHEMA.keywords)
    assert [item.label.value for item in labelled] == ["kept"]


def test_labelled_bnode_with_name_keeps_label_without_id() -> None:
    graph = Graph()
    subject = URIRef("https://example.org/ds")
    blank = BNode()
    graph.add((subject, SCHEMA.keywords, blank))
    graph.add((blank, SCHEMA.name, Literal("Named Keyword")))
    labelled = _wrap(graph).view(subject).labelled(SCHEMA.keywords)
    assert len(labelled) == 1
    assert labelled[0].label.value == "Named Keyword"
    assert labelled[0].stable_id is None


def test_doi_from_property_value() -> None:
    graph = Graph()
    dataset = URIRef("https://example.org/ds")
    pv = BNode()
    graph.add((dataset, SCHEMA.identifier, pv))
    graph.add((pv, RDF.type, SCHEMA.PropertyValue))
    graph.add((pv, SCHEMA.propertyID, Literal("https://registry.identifiers.org/registry/doi")))
    graph.add((pv, SCHEMA.value, Literal("10.3220/253-2025-42")))
    dois = _wrap(graph).view(dataset).schema_dois("identifier")
    assert dois == ["10.3220/253-2025-42"]


def test_doi_property_value_ignores_blank_node_fields() -> None:
    graph = Graph()
    dataset = URIRef("https://example.org/ds")
    pv = BNode()
    graph.add((dataset, SCHEMA.identifier, pv))
    graph.add((pv, RDF.type, SCHEMA.PropertyValue))
    graph.add((pv, SCHEMA.propertyID, BNode()))
    graph.add((pv, SCHEMA.value, BNode()))
    assert _wrap(graph).view(dataset).schema_dois("identifier") == []
    assert _wrap(graph).view(pv).doi() is None


def test_doi_blank_without_fields_is_none() -> None:
    graph = Graph()
    blank = BNode()
    assert _wrap(graph).view(blank).doi() is None


def test_http_iri_rejects_bnode() -> None:
    assert _wrap(Graph()).view(BNode()).http_iri() is None
    uri = URIRef("https://example.org/x")
    assert _wrap(Graph()).view(uri).http_iri() == "https://example.org/x"


def test_dual_schema_org_namespaces() -> None:
    graph = Graph()
    subject = URIRef("https://example.org/ds")
    graph.add((subject, SCHEMA_HTTP.name, Literal("Http Name")))
    graph.add((subject, SCHEMA.keywords, Literal("kw")))
    view = _wrap(graph).view(subject)
    assert view.schema_text("name") == "Http Name"
    assert view["name"] == "Http Name"
    assert view.schema_texts("keywords") == ["kw"]
