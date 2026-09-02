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


def test_text_resolves_labelled_blank_object() -> None:
    graph = Graph()
    dataset = URIRef("https://example.org/ds")
    license_node = BNode()
    graph.add((dataset, SCHEMA.license, license_node))
    graph.add((license_node, SCHEMA.name, Literal("CC BY 4.0")))
    view = _wrap(graph).view(dataset)
    assert view.text(SCHEMA.license) == "CC BY 4.0"
    assert view.schema_text("license") == "CC BY 4.0"
    assert view.texts(SCHEMA.license) == ["CC BY 4.0"]


def test_text_skips_unlabelled_blank_object() -> None:
    graph = Graph()
    dataset = URIRef("https://example.org/ds")
    graph.add((dataset, SCHEMA.license, BNode()))
    view = _wrap(graph).view(dataset)
    assert view.text(SCHEMA.license) is None
    assert view.schema_text("license") is None
    assert view.texts(SCHEMA.license) == []


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


def test_doi_ignores_property_id_value_without_property_value_type() -> None:
    graph = Graph()
    dataset = URIRef("https://example.org/ds")
    not_pv = BNode()
    graph.add((dataset, SCHEMA.identifier, not_pv))
    graph.add((not_pv, SCHEMA.propertyID, Literal("https://registry.identifiers.org/registry/doi")))
    graph.add((not_pv, SCHEMA.value, Literal("10.3220/253-2025-42")))
    assert _wrap(graph).view(dataset).schema_dois("identifier") == []
    assert _wrap(graph).view(not_pv).doi() is None


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


def test_subjects_of_type_orders_by_sort_key_not_insert_order() -> None:
    def ids(order: list[str]) -> list[str]:
        graph = Graph()
        for iri in order:
            subject = URIRef(iri)
            graph.add((subject, RDF.type, SCHEMA.Dataset))
            graph.add((subject, SCHEMA.name, Literal(iri.rsplit("/", maxsplit=1)[-1])))
        return [view.iri or "" for view in _wrap(graph).subjects_of_type(SCHEMA.Dataset)]

    left = ["https://example.org/dataset/zeta", "https://example.org/dataset/alpha"]
    right = list(reversed(left))
    assert (
        ids(left)
        == ids(right)
        == [
            "https://example.org/dataset/alpha",
            "https://example.org/dataset/zeta",
        ]
    )


def test_subjects_of_types_dedupes_dual_namespace_dataset() -> None:
    graph = Graph()
    subject = URIRef("https://example.org/dataset/both")
    graph.add((subject, RDF.type, SCHEMA.Dataset))
    graph.add((subject, RDF.type, SCHEMA_HTTP.Dataset))
    graph.add((subject, SCHEMA.name, Literal("Both")))
    views = _wrap(graph).subjects_of_types(SCHEMA.Dataset, SCHEMA_HTTP.Dataset)
    assert [view.iri for view in views] == ["https://example.org/dataset/both"]


def test_subjects_predicate_object_is_ordered() -> None:
    content_type = URIRef("http://example.org/vocab#contentType")
    marker = Literal("researchData")

    def ids(order: list[str]) -> list[str]:
        graph = Graph()
        for iri in order:
            graph.add((URIRef(iri), content_type, marker))
        return [view.iri or "" for view in StableGraph.wrap(graph).subjects(content_type, marker)]

    left = ["https://example.org/b", "https://example.org/a"]
    assert (
        ids(left)
        == ids(list(reversed(left)))
        == [
            "https://example.org/a",
            "https://example.org/b",
        ]
    )
