"""Schema.org mapper unit tests."""

import json
import re
from pathlib import Path

import pytest
from arctrl import ARC  # type: ignore[import-untyped]
from arctrl.py.ContractIO.contract_io import full_fill_contract_batch_async  # type: ignore[import-untyped]
from fable_library.async_ import run_synchronously  # type: ignore[import-untyped]
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


_BLANK_NODE_ID = re.compile(r"^N[0-9a-fA-F]{32}$")

_OPENAGRAR_PROPERTYVALUE_DOI = """
{
  "@context": "https://schema.org/",
  "@type": "Dataset",
  "name": "Flower visitors in legume-intercrops",
  "identifier": [{
    "@type": "PropertyValue",
    "propertyID": "https://registry.identifiers.org/registry/doi",
    "value": "10.3220/253-2025-42"
  }]
}
"""


def _parse_jsonld(payload: str) -> Graph:
    graph = Graph()
    graph.parse(data=payload, format="json-ld")
    return graph


def _root_identifier(arc_json: str) -> str:
    payload = json.loads(arc_json)
    root = next(item for item in payload["@graph"] if item.get("@id") == "./")
    identifier = root["identifier"]
    assert isinstance(identifier, str)
    return identifier


def test_openagrar_propertyvalue_doi_is_investigation_identifier() -> None:
    graph = _parse_jsonld(_OPENAGRAR_PROPERTYVALUE_DOI)
    subject = None
    for schema in GeneralSchemaOrgMapper.SCHEMA_URIS:
        subjects = list(graph.subjects(RDF.type, schema.Dataset))
        if subjects:
            subject = subjects[0]
            break
    assert isinstance(subject, BNode)

    harvested = GeneralSchemaOrgMapper().map_graph(graph)
    identifier = _root_identifier(harvested.arc_json)

    assert identifier == "10.3220/253-2025-42"
    assert not _BLANK_NODE_ID.fullmatch(identifier)
    assert harvested.identifier == "10.3220/253-2025-42"
    # With only DOI (no @id/url/sameAs on the Dataset blank node), the Measurement
    # table output URI must still be meaningful (no empty `URI=` cell).
    assert '"@id":"URI=https://doi.org/10.3220/253-2025-42"' in harvested.arc_json
    assert '"@id":"URI="' not in harvested.arc_json


def test_openagrar_propertyvalue_doi_is_stable_across_parses() -> None:
    first = _root_identifier(GeneralSchemaOrgMapper().map_graph(_parse_jsonld(_OPENAGRAR_PROPERTYVALUE_DOI)).arc_json)
    second = _root_identifier(GeneralSchemaOrgMapper().map_graph(_parse_jsonld(_OPENAGRAR_PROPERTYVALUE_DOI)).arc_json)
    assert first == second == "10.3220/253-2025-42"


def test_openagrar_without_doi_uses_full_receive_url() -> None:
    graph = _parse_jsonld(
        """
        {
          "@context": "https://schema.org/",
          "@type": "Dataset",
          "name": "C-Module"
        }
        """
    )
    source_url = "https://www.openagrar.de/receive/openagrar_mods_00107322"
    harvested = GeneralSchemaOrgMapper().map_graph(graph, source_url=source_url)
    identifier = _root_identifier(harvested.arc_json)
    assert identifier == "www_openagrar_de_receive_openagrar_mods_00107322"
    assert not _BLANK_NODE_ID.fullmatch(identifier)


def test_schema_org_without_stable_identifier_raises_and_does_not_use_blank_node() -> None:
    graph = _parse_jsonld(
        """
        {
          "@context": "https://schema.org/",
          "@type": "Dataset",
          "name": "C-Module"
        }
        """
    )
    mapper = GeneralSchemaOrgMapper()
    with pytest.raises(ValueError, match="no stable identifier"):
        mapper.map_graph(graph)


def test_http_dataset_id_is_kept_as_identifier() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))

    identifier = _root_identifier(GeneralSchemaOrgMapper().map_graph(graph).arc_json)
    assert identifier == "example_org_dataset_1"


def test_assay_table_falls_back_to_dataset_iri_when_schema_url_missing() -> None:
    """When schema:url is absent, Measurement["URI"] MUST not be empty for URIRef datasets."""
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))

    arc_json = GeneralSchemaOrgMapper().map_graph(graph).arc_json

    # arctrl encodes the output IOType("URI") as an @id that starts with `URI=`.
    assert '"@id":"URI=https://example.org/dataset/1"' in arc_json
    assert '"@id":"URI="' not in arc_json


def test_schema_url_is_preferred_over_http_identifier_literal() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = BNode()
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))
    graph.add((dataset, schema.identifier, Literal("https://example.org/other-id")))
    graph.add((dataset, schema.url, Literal("https://example.org/canonical")))

    identifier = _root_identifier(GeneralSchemaOrgMapper().map_graph(graph).arc_json)
    assert identifier == "example_org_canonical"


def test_propertyvalue_without_doi_property_id_is_not_treated_as_doi() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = BNode()
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))
    property_value = BNode()
    graph.add((dataset, schema.identifier, property_value))
    graph.add((property_value, RDF.type, schema.PropertyValue))
    graph.add((property_value, schema.value, Literal("10.3220/not-marked-as-doi")))

    with pytest.raises(ValueError, match="no stable identifier"):
        GeneralSchemaOrgMapper().map_graph(graph)


def test_named_property_value_with_doi_is_extracted() -> None:
    """A PropertyValue with a URIRef @id and propertyID=DOI must still yield its DOI."""
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = BNode()
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Named PV Dataset")))
    pv = URIRef("https://example.org/property-values/1")
    graph.add((dataset, schema.identifier, pv))
    graph.add((pv, RDF.type, schema.PropertyValue))
    graph.add((pv, schema.propertyID, Literal("DOI")))
    graph.add((pv, schema.value, Literal("10.1234/named-pv")))

    identifier = _root_identifier(GeneralSchemaOrgMapper().map_graph(graph).arc_json)
    assert identifier == "10.1234/named-pv"


def _keywords_comment_text(arc_json: str) -> str | None:
    payload = json.loads(arc_json)
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Comment" not in type_list:
            continue
        name = str(item.get("name") or "")
        if name == "Keywords":
            return str(item.get("text") or "")
    return None


def _keywords_derived_ids(arc_json: str) -> list[str]:
    """Return sorted @ids of Keywords Comment / ParameterValue nodes (hash-relevant)."""
    payload = json.loads(arc_json)
    ids: list[str] = []
    for item in payload.get("@graph", []):
        node_id = str(item.get("@id") or "")
        if "Keywords" in node_id and node_id.startswith(("#LDComment_Keywords", "#ParameterValue_Keywords")):
            ids.append(node_id)
    return sorted(ids)


def _investigation_description(arc_json: str) -> str:
    payload = json.loads(arc_json)
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Investigation" in type_list or "Dataset" in type_list:
            desc = item.get("description")
            if desc is not None:
                return str(desc)
    # Fallback: search description fields
    for item in payload.get("@graph", []):
        if "description" in item and item.get("@type") not in (None, "Comment"):
            return str(item["description"])
    return ""


def _contact_name_pairs(arc_json: str) -> list[tuple[str, str]]:
    payload = json.loads(arc_json)
    pairs: list[tuple[str, str]] = []
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Person" not in type_list:
            continue
        person_id = str(item.get("@id") or "")
        if person_id.startswith("#Author_"):
            continue
        given = str(item.get("givenName") or "")
        family = str(item.get("familyName") or "")
        if given or family:
            pairs.append((given, family))
    return pairs


def _publication_author_node_id(arc_json: str) -> str | None:
    payload = json.loads(arc_json)
    for item in payload.get("@graph", []):
        person_id = str(item.get("@id") or "")
        if person_id.startswith("#Author_"):
            return person_id
    return None


def _publisher_comment_text(arc_json: str) -> str | None:
    payload = json.loads(arc_json)
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Comment" not in type_list:
            continue
        if str(item.get("name") or "") == "Publisher":
            return str(item.get("text") or "")
    return None


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

    first = GeneralSchemaOrgMapper().map_graph(build(["zeta", "alpha", "Beta"])).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build(["Beta", "zeta", "alpha"])).arc_json
    assert _keywords_comment_text(first) == _keywords_comment_text(second) == "alpha, Beta, zeta"
    assert _keywords_derived_ids(first) == _keywords_derived_ids(second)
    assert _keywords_derived_ids(first), "expected Keywords Comment and/or ParameterValue @ids"


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
    first = GeneralSchemaOrgMapper().map_graph(build(literals_a)).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build(literals_b)).arc_json
    assert _investigation_description(first) == _investigation_description(second) == "English description"
    assert "Deutsche" not in _investigation_description(first)


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
    first = GeneralSchemaOrgMapper().map_graph(build(order_a)).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build(order_b)).arc_json
    assert _contact_name_pairs(first) == _contact_name_pairs(second) == [("Ada", "Lovelace"), ("Zed", "Zebra")]
    assert _publication_author_node_id(first) == _publication_author_node_id(second)
    assert _publication_author_node_id(first) == "#Author_A. Lovelace; Z. Zebra"
    assert "," not in (_publication_author_node_id(first) or "")


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

    first = GeneralSchemaOrgMapper().map_graph(graph).arc_json
    second = GeneralSchemaOrgMapper().map_graph(graph).arc_json
    assert _keywords_comment_text(first) == _keywords_comment_text(second) == "intercrop, legume, pollinators"
    assert _keywords_derived_ids(first) == _keywords_derived_ids(second)
    assert _investigation_description(first) == _investigation_description(second) == "Full English abstract"
    assert _contact_name_pairs(first) == _contact_name_pairs(second)
    assert _publication_author_node_id(first) == _publication_author_node_id(second)


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

    assert _publisher_comment_text(GeneralSchemaOrgMapper().map_graph(graph).arc_json) == "Named Org"


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

    first = GeneralSchemaOrgMapper().map_graph(build(["Zeta Org", "Alpha Org"])).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build(["Alpha Org", "Zeta Org"])).arc_json
    assert _publisher_comment_text(first) == _publisher_comment_text(second) == "Alpha Org"


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

    first = GeneralSchemaOrgMapper().map_graph(build([("Zed", "Zebra"), ("Ada", "Lovelace")])).arc_json
    second = GeneralSchemaOrgMapper().map_graph(build([("Ada", "Lovelace"), ("Zed", "Zebra")])).arc_json
    assert _contact_name_pairs(first) == _contact_name_pairs(second) == [("Ada", "Lovelace"), ("Zed", "Zebra")]
    assert _publication_author_node_id(first) == _publication_author_node_id(second) == "#Author_A. Lovelace; Z. Zebra"
