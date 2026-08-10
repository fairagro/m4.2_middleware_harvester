"""Schema.org mapper unit tests."""

import json
from pathlib import Path

import pytest
from arctrl import ARC  # type: ignore[import-untyped]
from arctrl.py.ContractIO.contract_io import full_fill_contract_batch_async  # type: ignore[import-untyped]
from arctrl.py.fable_modules.fable_library.async_ import run_synchronously  # type: ignore[import-untyped]
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
    result = mapper.map_graph(graph).arc_json

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
    result = mapper.map_graph(graph).arc_json
    payload = json.loads(result)

    assert "@graph" in payload
    root = next(item for item in payload["@graph"] if item.get("@id") == "./")
    assert root["identifier"] == "10.1234/abc"
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
    harvested = mapper.map_graph(_openagrar_like_graph())
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
        mapper.map_graph(graph)


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

    payload = json.loads(GeneralSchemaOrgMapper().map_graph(graph).arc_json)
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
        mapper.map_graph(graph)


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

    text = GeneralSchemaOrgMapper().map_graph(graph).arc_json
    assert "Thünen Institute" in text
    payload = json.loads(text)
    people = [
        item
        for item in payload["@graph"]
        if item.get("@type") == "Person" or (isinstance(item.get("@type"), list) and "Person" in item.get("@type", []))
    ]
    assert len(people) == 1
    assert people[0].get("givenName") == "Jonas"
