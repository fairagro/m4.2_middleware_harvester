"""Schema.org mapper unit tests."""

import json
import re
from pathlib import Path

import pytest
from arctrl import ARC  # type: ignore[import-untyped]
from arctrl.py.ContractIO.contract_io import full_fill_contract_batch_async  # type: ignore[import-untyped]
from fable_library.async_ import run_synchronously  # type: ignore[import-untyped]
from mapper_test_helpers import (
    NO_DISCOVERY,
    assert_stable_author_node_id,
    contact_name_pairs,
    investigation_description,
    keywords_comment_text,
    keywords_derived_ids,
    publication_author_node_id,
    publisher_comment_text,
)
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.linked_data.linked_data_mapper import GeneralSchemaOrgMapper


def test_general_mapper_returns_jsonld() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))
    creator = URIRef("https://example.org/person/1")
    graph.add((dataset, schema.creator, creator))
    graph.add((creator, RDF.type, schema.Person))
    graph.add((creator, schema.givenName, Literal("Ada")))
    graph.add((creator, schema.familyName, Literal("Lovelace")))

    mapper = GeneralSchemaOrgMapper()
    result = mapper.map_graph(graph, NO_DISCOVERY).arc_json

    assert result.startswith("{") and "@context" in result


def test_general_mapper_raises_when_no_dataset_entity_present() -> None:
    graph = Graph()

    mapper = GeneralSchemaOrgMapper()
    with pytest.raises(ValueError, match="Graph does not contain a Schema.org Dataset entity"):
        mapper.map_graph(graph, NO_DISCOVERY)


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
    result = mapper.map_graph(graph, NO_DISCOVERY).arc_json
    payload = json.loads(result)

    assert "@graph" in payload
    root = next(item for item in payload["@graph"] if item.get("@id") == "./")
    assert root["identifier"] == "example_org_dataset_1"
    assert "CC-BY" in result
    assert "Publisher Co" in result
    people = [
        item
        for item in payload["@graph"]
        if item.get("@type") == "Person" or (isinstance(item.get("@type"), list) and "Person" in item.get("@type", []))
    ]
    assert all(str(p.get("givenName", "")).strip() for p in people)
    assert not any(p.get("familyName") == "Publisher Co" for p in people)


def _openagrar_like_graph() -> Graph:
    """Person creators with givenName + Organization publisher Zenodo (OpenAgrar shape)."""
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://www.openagrar.de/receive/openagrar_mods_00108560")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("OpenAgrar Example Dataset")))

    for given, family, pid in [
        ("Jonas", "Niklewski", "1"),
        ("Seyyed Hasan", "Hosseini", "2"),
        ("Christian", "Brischke", "3"),
    ]:
        person = URIRef(f"https://example.org/author/{pid}")
        graph.add((dataset, schema.creator, person))
        graph.add((person, RDF.type, schema.Person))
        graph.add((person, schema.givenName, Literal(given)))
        graph.add((person, schema.familyName, Literal(family)))

    publisher = URIRef("https://zenodo.org")
    graph.add((publisher, RDF.type, schema.Organization))
    graph.add((publisher, schema.name, Literal("Zenodo")))
    graph.add((publisher, schema.url, Literal("https://zenodo.org")))
    graph.add((dataset, schema.publisher, publisher))
    return graph


def test_openagrar_like_publisher_is_comment_not_empty_given_person(tmp_path: Path) -> None:
    mapper = GeneralSchemaOrgMapper()
    harvested = mapper.map_graph(_openagrar_like_graph(), NO_DISCOVERY)
    payload = json.loads(harvested.arc_json)
    people = [
        item
        for item in payload["@graph"]
        if item.get("@type") == "Person" or (isinstance(item.get("@type"), list) and "Person" in item.get("@type", []))
    ]
    assert len(people) == 3
    assert all(str(p.get("givenName", "")).strip() for p in people)
    assert not any(p.get("familyName") == "Zenodo" for p in people)
    assert "Zenodo" in harvested.arc_json

    arc = ARC.from_rocrate_json_string(harvested.arc_json)
    contracts = list(arc.GetWriteContracts())
    run_synchronously(full_fill_contract_batch_async(False, str(tmp_path), contracts))
    loaded = ARC.load(str(tmp_path))
    # Must not raise: Person must have a given name
    reloaded = loaded.ToROCrateJsonString()
    assert "Niklewski" in reloaded
    assert '"givenName": ""' not in reloaded


def test_author_without_given_name_fails_mapping() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/no-given")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("No Given Name")))
    author = URIRef("https://example.org/author/x")
    graph.add((dataset, schema.creator, author))
    graph.add((author, RDF.type, schema.Person))
    graph.add((author, schema.familyName, Literal("OnlyLast")))

    mapper = GeneralSchemaOrgMapper()
    with pytest.raises(ValueError, match="non-empty given name"):
        mapper.map_graph(graph, NO_DISCOVERY)


def test_family_name_with_display_name_recovers_given_name() -> None:
    """Recover given name from schema:name when givenName is missing but familyName is set."""
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/display-name")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Display Name Fallback")))
    author = URIRef("https://example.org/author/ada")
    graph.add((dataset, schema.creator, author))
    graph.add((author, RDF.type, schema.Person))
    graph.add((author, schema.familyName, Literal("Lovelace")))
    graph.add((author, schema.name, Literal("Ada Lovelace")))

    payload = json.loads(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json)
    people = [
        item
        for item in payload["@graph"]
        if item.get("@type") == "Person" or (isinstance(item.get("@type"), list) and "Person" in item.get("@type", []))
    ]
    assert len(people) == 1
    assert people[0].get("givenName") == "Ada"
    assert people[0].get("familyName") == "Lovelace"


def test_single_token_literal_creator_fails_mapping() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/literal")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Literal Creator")))
    graph.add((dataset, schema.creator, Literal("Zenodo")))

    mapper = GeneralSchemaOrgMapper()
    with pytest.raises(ValueError, match="non-empty given name"):
        mapper.map_graph(graph, NO_DISCOVERY)


def test_creator_affiliation_preserved_on_person() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/aff")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Affiliated")))
    person = URIRef("https://example.org/author/a")
    org = URIRef("https://example.org/org/thuenen")
    graph.add((dataset, schema.creator, person))
    graph.add((person, RDF.type, schema.Person))
    graph.add((person, schema.givenName, Literal("Jonas")))
    graph.add((person, schema.familyName, Literal("Niklewski")))
    graph.add((person, schema.affiliation, org))
    graph.add((org, RDF.type, schema.Organization))
    graph.add((org, schema.name, Literal("Thünen Institute")))

    text = GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json
    assert "Thünen Institute" in text
    payload = json.loads(text)
    people = [
        item
        for item in payload["@graph"]
        if item.get("@type") == "Person" or (isinstance(item.get("@type"), list) and "Person" in item.get("@type", []))
    ]
    assert len(people) == 1
    assert people[0].get("givenName") == "Jonas"


def test_keywords_order_invariant() -> None:
    schema = Namespace("https://schema.org/")

    def build(order: list[str]) -> Graph:
        graph = Graph()
        dataset = URIRef("https://example.org/kw")
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("KW Dataset")))
        graph.add((dataset, schema.identifier, Literal("10.9/kw")))
        for keyword in order:
            graph.add((dataset, schema.keywords, Literal(keyword)))
        return graph

    first = GeneralSchemaOrgMapper().map_graph(build(["zeta", "alpha", "Beta"]), NO_DISCOVERY).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build(["Beta", "zeta", "alpha"]), NO_DISCOVERY).arc_json
    assert keywords_comment_text(first) == keywords_comment_text(second) == "alpha, Beta, zeta"
    assert keywords_derived_ids(first) == keywords_derived_ids(second)
    assert keywords_derived_ids(first), "expected Keywords Comment and/or ParameterValue @ids"


def test_description_prefers_en_over_de_and_skips_empty() -> None:
    schema = Namespace("https://schema.org/")

    def build(desc_order: list[Literal]) -> Graph:
        graph = Graph()
        dataset = URIRef("https://example.org/desc")
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("Desc Dataset")))
        graph.add((dataset, schema.identifier, Literal("10.9/desc")))
        for literal in desc_order:
            graph.add((dataset, schema.description, literal))
        return graph

    literals_a = [
        Literal(""),
        Literal("Deutsche Beschreibung", lang="de"),
        Literal("English description", lang="en"),
    ]
    literals_b = list(reversed(literals_a))
    first = GeneralSchemaOrgMapper().map_graph(build(literals_a), NO_DISCOVERY).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build(literals_b), NO_DISCOVERY).arc_json
    assert investigation_description(first) == investigation_description(second) == "English description"
    assert "Deutsche" not in investigation_description(first)


def test_contacts_and_publication_authors_order_invariant() -> None:
    schema = Namespace("https://schema.org/")

    def build(creator_order: list[tuple[str, str, str]]) -> Graph:
        graph = Graph()
        dataset = URIRef("https://example.org/people")
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("People Dataset")))
        graph.add((dataset, schema.identifier, Literal("10.9/people")))
        for uri, given, family in creator_order:
            person = URIRef(uri)
            graph.add((dataset, schema.creator, person))
            graph.add((person, RDF.type, schema.Person))
            graph.add((person, schema.givenName, Literal(given)))
            graph.add((person, schema.familyName, Literal(family)))
        return graph

    order_a = [
        ("https://example.org/p/2", "Zed", "Zebra"),
        ("https://example.org/p/1", "Ada", "Lovelace"),
    ]
    order_b = list(reversed(order_a))
    first = GeneralSchemaOrgMapper().map_graph(build(order_a), NO_DISCOVERY).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build(order_b), NO_DISCOVERY).arc_json
    assert contact_name_pairs(first) == contact_name_pairs(second) == [("Ada", "Lovelace"), ("Zed", "Zebra")]
    assert publication_author_node_id(first) == publication_author_node_id(second)
    assert_stable_author_node_id(publication_author_node_id(first), "A. Lovelace; Z. Zebra")


def test_double_map_openagrar_like_fixture_is_stable() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = BNode()
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Flower visitors")))
    graph.add((dataset, schema.identifier, Literal("10.3220/253-2025-42")))
    graph.add((dataset, schema.description, Literal("", lang="en")))
    graph.add((dataset, schema.description, Literal("Kurztext", lang="de")))
    graph.add((dataset, schema.description, Literal("Full English abstract", lang="en")))
    for keyword in ("pollinators", "legume", "intercrop"):
        graph.add((dataset, schema.keywords, Literal(keyword)))
    for uri, given, family in (
        ("https://example.org/a", "Jonas", "Niklewski"),
        ("https://example.org/b", "Anna", "Meier"),
    ):
        person = URIRef(uri)
        graph.add((dataset, schema.creator, person))
        graph.add((person, RDF.type, schema.Person))
        graph.add((person, schema.givenName, Literal(given)))
        graph.add((person, schema.familyName, Literal(family)))

    first = GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json
    second = GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json
    assert keywords_comment_text(first) == keywords_comment_text(second) == "intercrop, legume, pollinators"
    assert keywords_derived_ids(first) == keywords_derived_ids(second)
    assert investigation_description(first) == investigation_description(second) == "Full English abstract"
    assert contact_name_pairs(first) == contact_name_pairs(second)
    assert publication_author_node_id(first) == publication_author_node_id(second)


def test_obj_prefers_uriref_publisher_over_blank_node() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/pub-mix")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Mix Publisher Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/pub-mix")))

    blank = BNode()
    graph.add((dataset, schema.publisher, blank))
    graph.add((blank, RDF.type, schema.Organization))
    graph.add((blank, schema.name, Literal("Blank Org")))

    named = URIRef("https://example.org/org/named")
    graph.add((dataset, schema.publisher, named))
    graph.add((named, RDF.type, schema.Organization))
    graph.add((named, schema.name, Literal("Named Org")))

    assert publisher_comment_text(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json) == "Named Org"


def test_obj_blank_publisher_choice_stable_across_fresh_bnode_labels() -> None:
    schema = Namespace("https://schema.org/")

    def build(name_order: list[str]) -> Graph:
        graph = Graph()
        dataset = URIRef("https://example.org/pub-bnodes")
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("BNode Publisher Dataset")))
        graph.add((dataset, schema.identifier, Literal("10.9/pub-bnodes")))
        for name in name_order:
            publisher = BNode()
            graph.add((dataset, schema.publisher, publisher))
            graph.add((publisher, RDF.type, schema.Organization))
            graph.add((publisher, schema.name, Literal(name)))
        return graph

    first = GeneralSchemaOrgMapper().map_graph(build(["Zeta Org", "Alpha Org"]), NO_DISCOVERY).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build(["Alpha Org", "Zeta Org"]), NO_DISCOVERY).arc_json
    assert publisher_comment_text(first) == publisher_comment_text(second) == "Alpha Org"


def test_obj_nested_blank_publisher_choice_uses_nested_literals() -> None:
    """BNode→BNode edges must affect selection when direct literals would rank opposite."""
    schema = Namespace("https://schema.org/")

    def build(entries: list[tuple[str, str]]) -> Graph:
        # entries: (addressLocality, org name)
        graph = Graph()
        dataset = URIRef("https://example.org/pub-nested")
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("Nested BNode Publisher Dataset")))
        graph.add((dataset, schema.identifier, Literal("10.9/pub-nested")))
        for city, org_name in entries:
            publisher = BNode()
            address = BNode()
            graph.add((dataset, schema.publisher, publisher))
            graph.add((publisher, RDF.type, schema.Organization))
            graph.add((publisher, schema.name, Literal(org_name)))
            graph.add((publisher, schema.address, address))
            graph.add((address, schema.addressLocality, Literal(city)))
        return graph

    # Direct name alone would prefer "Aaa Org"; nested locality prefers Amsterdam → "Zzz Org".
    entries_a = [("Zurich", "Aaa Org"), ("Amsterdam", "Zzz Org")]
    entries_b = list(reversed(entries_a))
    first = GeneralSchemaOrgMapper().map_graph(build(entries_a), NO_DISCOVERY).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build(entries_b), NO_DISCOVERY).arc_json
    assert publisher_comment_text(first) == publisher_comment_text(second) == "Zzz Org"


def test_stable_node_sort_key_distinguishes_literal_language_tags() -> None:
    """Same lexical value, different language tags must not collide in signatures."""
    from middleware.linked_data.linked_data_mapper.stable_graph import SCHEMA_ORG_NAMESPACES, StableGraph

    schema = Namespace("https://schema.org/")
    graph = Graph()
    left = BNode()
    right = BNode()
    graph.add((left, schema.name, Literal("Same", lang="en")))
    graph.add((right, schema.name, Literal("Same", lang="de")))
    sg = StableGraph.wrap(graph, term_namespaces=SCHEMA_ORG_NAMESPACES)
    left_key = sg.view(left).sort_key()
    right_key = sg.view(right).sort_key()
    assert left_key != right_key
    assert "'en'" in left_key[1]
    assert "'de'" in right_key[1]


def test_stable_node_sort_key_no_delimiter_collision() -> None:
    """Predicate/literal structures must not collapse to the same signature string."""
    from middleware.linked_data.linked_data_mapper.stable_graph import StableGraph

    graph = Graph()
    left = BNode()
    right = BNode()
    graph.add((left, URIRef("http://ex/a"), Literal("b=c")))
    graph.add((right, URIRef("http://ex/a=b"), Literal("c")))
    sg = StableGraph.wrap(graph)
    left_key = sg.view(left).sort_key()
    right_key = sg.view(right).sort_key()
    assert left_key != right_key


def test_stable_term_token_no_literal_encoding_collision() -> None:
    """Crafted literal text must not mimic structured lang/datatype encoding."""
    from middleware.linked_data.linked_data_mapper.stable_graph import _stable_term_token

    crafted = Literal("a|lang=|dt=x", datatype=URIRef("y"))
    structured = Literal("a", datatype=URIRef("x|lang=|dt=y"))
    crafted_token = _stable_term_token(crafted)
    structured_token = _stable_term_token(structured)
    assert crafted_token is not None
    assert structured_token is not None
    assert crafted_token != structured_token


def test_strs_uses_bnode_schema_name_and_skips_unlabelled_bnodes() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/kw-bnodes")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Keyword BNode Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/kw-bnodes")))

    labelled = BNode()
    graph.add((dataset, schema.keywords, labelled))
    graph.add((labelled, schema.name, Literal("DefinedTerm Keyword")))

    unlabelled = BNode()
    graph.add((dataset, schema.keywords, unlabelled))

    nested_name = BNode()
    nested_term = BNode()
    graph.add((dataset, schema.keywords, nested_term))
    graph.add((nested_term, schema.name, nested_name))  # name is itself a BNode → skip

    graph.add((dataset, schema.keywords, Literal("literal-kw")))

    arc_json = GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json
    assert keywords_comment_text(arc_json) == "DefinedTerm Keyword, literal-kw"
    assert not re.search(r"\bN[0-9a-fA-F]{32}\b", keywords_comment_text(arc_json) or "")
    assert "_:" not in (keywords_comment_text(arc_json) or "")


def test_publisher_uriref_without_name_is_kept() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/pub-iri")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Publisher IRI Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/pub-iri")))
    publisher = URIRef("https://example.org/org/nameless")
    graph.add((dataset, schema.publisher, publisher))
    graph.add((publisher, RDF.type, schema.Organization))

    assert publisher_comment_text(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json) == (
        "https://example.org/org/nameless"
    )


def test_publisher_unlabelled_bnode_without_name_is_skipped() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/pub-blank")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Publisher Blank Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/pub-blank")))
    publisher = BNode()
    graph.add((dataset, schema.publisher, publisher))
    graph.add((publisher, RDF.type, schema.Organization))

    arc_json = GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json
    assert publisher_comment_text(arc_json) is None
    assert not re.search(r"#LDComment_Publisher_N[0-9a-fA-F]{32}", arc_json)


def test_publisher_prefers_organization_name_over_literal_for_processing_note() -> None:
    """Literal + Organization: tables/notes must use the Organization name, not skip via _obj."""
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/pub-both")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Dual Publisher Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/pub-both")))
    graph.add((dataset, schema.publisher, Literal("string-publisher")))
    org = URIRef("https://example.org/org/zenodo")
    graph.add((dataset, schema.publisher, org))
    graph.add((org, RDF.type, schema.Organization))
    graph.add((org, schema.name, Literal("Zenodo")))

    arc_json = GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json
    assert publisher_comment_text(arc_json) == "Zenodo"
    assert "Publisher: Zenodo" in arc_json
    assert "Publisher: string-publisher" not in arc_json
    assert "Unknown Publisher" not in arc_json


def test_literal_only_publisher_enriches_processing_note() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/pub-lit")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Literal Publisher Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/pub-lit")))
    graph.add((dataset, schema.publisher, Literal("Literal Press")))

    arc_json = GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json
    assert publisher_comment_text(arc_json) == "Literal Press"
    assert "Publisher: Literal Press" in arc_json


def test_publisher_falls_back_to_literal_when_organization_bnode_has_no_name() -> None:
    schema = Namespace("https://schema.org/")
    graph = Graph()
    dataset = URIRef("https://example.org/pub-org-blank-lit")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Org Blank Plus Literal Dataset")))
    graph.add((dataset, schema.identifier, Literal("10.9/pub-org-blank-lit")))
    blank_org = BNode()
    graph.add((dataset, schema.publisher, blank_org))
    graph.add((blank_org, RDF.type, schema.Organization))
    graph.add((dataset, schema.publisher, Literal("Fallback Press")))

    arc_json = GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY).arc_json
    assert publisher_comment_text(arc_json) == "Fallback Press"
    assert "Publisher: Fallback Press" in arc_json


def test_blank_node_creators_sort_stable_without_bnode_labels() -> None:
    schema = Namespace("https://schema.org/")

    def build(creator_order: list[tuple[str, str]]) -> Graph:
        graph = Graph()
        dataset = URIRef("https://example.org/people-bnodes")
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("BNode People Dataset")))
        graph.add((dataset, schema.identifier, Literal("10.9/people-bnodes")))
        for given, family in creator_order:
            person = BNode()
            graph.add((dataset, schema.creator, person))
            graph.add((person, RDF.type, schema.Person))
            graph.add((person, schema.givenName, Literal(given)))
            graph.add((person, schema.familyName, Literal(family)))
        return graph

    first = GeneralSchemaOrgMapper().map_graph(build([("Zed", "Zebra"), ("Ada", "Lovelace")]), NO_DISCOVERY).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build([("Ada", "Lovelace"), ("Zed", "Zebra")]), NO_DISCOVERY).arc_json
    assert contact_name_pairs(first) == contact_name_pairs(second) == [("Ada", "Lovelace"), ("Zed", "Zebra")]
