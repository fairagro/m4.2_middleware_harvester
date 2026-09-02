"""Schema.org mapper identifier resolution unit tests."""

import pytest
from mapper_test_helpers import (
    BLANK_NODE_ID,
    NO_DISCOVERY,
    OPENAGRAR_PROPERTYVALUE_DOI,
    alternate_identifier_values,
    dual_doi_payload,
    first_harvest,
    pangaea_doi_graph,
    parse_jsonld,
    root_identifier,
)
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.linked_data.linked_data_mapper import GeneralSchemaOrgMapper, LinkedDataMapper, MappingContext


def test_pick_canonical_doi_casefold_ties_prefer_lexicographic_original() -> None:
    left = ["10.1234/Ab", "10.1234/ab"]
    right = list(reversed(left))
    assert LinkedDataMapper.pick_canonical_doi(left) == LinkedDataMapper.pick_canonical_doi(right) == "10.1234/Ab"


def test_openagrar_with_doi_uses_harvest_source_id_not_doi() -> None:
    source_url = "https://www.openagrar.de/receive/openagrar_mods_00107322"
    harvested = first_harvest(
        GeneralSchemaOrgMapper().map_graph(
            parse_jsonld(OPENAGRAR_PROPERTYVALUE_DOI),
            MappingContext(
                source_url=source_url,
                harvest_source_id="openagrar_mods_00107322",
            ),
        )
    )
    identifier = root_identifier(harvested.arc_json)
    assert identifier == "openagrar_mods_00107322"
    assert identifier != "10.3220/253-2025-42"
    assert "10.3220/253-2025-42" in harvested.arc_json


def test_openagrar_propertyvalue_doi_is_investigation_identifier_when_no_source_url() -> None:
    graph = parse_jsonld(OPENAGRAR_PROPERTYVALUE_DOI)
    subject = None
    for schema in GeneralSchemaOrgMapper.SCHEMA_URIS:
        subjects = list(graph.subjects(RDF.type, schema.Dataset))
        if subjects:
            subject = subjects[0]
            break
    assert isinstance(subject, BNode)

    harvested = first_harvest(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY))
    identifier = root_identifier(harvested.arc_json)

    assert identifier == "10.3220/253-2025-42"
    assert not BLANK_NODE_ID.fullmatch(identifier)
    assert harvested.identifier == "10.3220/253-2025-42"
    assert '"@id":"URI=https://doi.org/10.3220/253-2025-42"' in harvested.arc_json
    assert '"@id":"URI="' not in harvested.arc_json


def test_openagrar_propertyvalue_doi_is_stable_across_parses() -> None:
    first = root_identifier(
        first_harvest(
            GeneralSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_PROPERTYVALUE_DOI), NO_DISCOVERY)
        ).arc_json
    )
    second = root_identifier(
        first_harvest(
            GeneralSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_PROPERTYVALUE_DOI), NO_DISCOVERY)
        ).arc_json
    )
    assert first == second == "10.3220/253-2025-42"


def test_openagrar_without_doi_uses_sanitized_source_url_without_pattern() -> None:
    graph = parse_jsonld(
        """
        {
          "@context": "https://schema.org/",
          "@type": "Dataset",
          "name": "C-Module"
        }
        """
    )
    source_url = "https://www.openagrar.de/receive/openagrar_mods_00107322"
    harvested = first_harvest(GeneralSchemaOrgMapper().map_graph(graph, MappingContext(source_url=source_url)))
    identifier = root_identifier(harvested.arc_json)
    assert identifier == "www_openagrar_de_receive_openagrar_mods_00107322"
    assert not BLANK_NODE_ID.fullmatch(identifier)


def test_openagrar_with_harvest_source_id_uses_catalog_id() -> None:
    graph = parse_jsonld(
        """
        {
          "@context": "https://schema.org/",
          "@type": "Dataset",
          "name": "C-Module"
        }
        """
    )
    source_url = "https://www.openagrar.de/receive/openagrar_mods_00107322"
    harvested = first_harvest(
        GeneralSchemaOrgMapper().map_graph(
            graph,
            MappingContext(
                source_url=source_url,
                harvest_source_id="openagrar_mods_00107322",
            ),
        )
    )
    identifier = root_identifier(harvested.arc_json)
    assert identifier == "openagrar_mods_00107322"


def test_schema_org_without_stable_identifier_raises_and_does_not_use_blank_node() -> None:
    graph = parse_jsonld(
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
        list(mapper.map_graph(graph, NO_DISCOVERY))


def test_http_dataset_id_is_kept_as_identifier() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))

    identifier = root_identifier(first_harvest(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY)).arc_json)
    assert identifier == "example_org_dataset_1"


def test_assay_table_falls_back_to_dataset_iri_when_schema_url_missing() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Example Dataset")))

    arc_json = first_harvest(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY)).arc_json
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

    identifier = root_identifier(first_harvest(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY)).arc_json)
    assert identifier == "example_org_canonical"


def test_multiple_schema_urls_pick_lexicographic_minimum_regardless_of_graph_order() -> None:
    schema = Namespace("https://schema.org/")

    def build(urls: list[str]) -> Graph:
        graph = Graph()
        dataset = BNode()
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("Multi URL Dataset")))
        for url in urls:
            graph.add((dataset, schema.url, Literal(url)))
        return graph

    first = root_identifier(
        first_harvest(
            GeneralSchemaOrgMapper().map_graph(
                build(["https://example.org/zeta", "https://example.org/alpha"]), NO_DISCOVERY
            )
        ).arc_json
    )
    second = root_identifier(
        first_harvest(
            GeneralSchemaOrgMapper().map_graph(
                build(["https://example.org/alpha", "https://example.org/zeta"]), NO_DISCOVERY
            )
        ).arc_json
    )
    assert first == second == "example_org_alpha"


def test_multiple_schema_urls_with_casefold_ties_are_stable() -> None:
    schema = Namespace("https://schema.org/")

    def build(urls: list[str]) -> Graph:
        graph = Graph()
        dataset = BNode()
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("Casefold tie URL Dataset")))
        for url in urls:
            graph.add((dataset, schema.url, Literal(url)))
        return graph

    urls_a = ["https://Example.org/Page", "https://example.org/page"]
    urls_b = list(reversed(urls_a))
    first = root_identifier(first_harvest(GeneralSchemaOrgMapper().map_graph(build(urls_a), NO_DISCOVERY)).arc_json)
    second = root_identifier(first_harvest(GeneralSchemaOrgMapper().map_graph(build(urls_b), NO_DISCOVERY)).arc_json)
    assert first == second == "Example_org_Page"


def test_assay_measurement_uri_stable_with_multiple_schema_urls() -> None:
    schema = Namespace("https://schema.org/")

    def build(urls: list[str]) -> Graph:
        graph = Graph()
        dataset = BNode()
        graph.add((dataset, RDF.type, schema.Dataset))
        graph.add((dataset, schema.name, Literal("Multi URL Assay Dataset")))
        for url in urls:
            graph.add((dataset, schema.url, Literal(url)))
        return graph

    first = first_harvest(
        GeneralSchemaOrgMapper().map_graph(
            build(["https://example.org/zeta", "https://example.org/alpha"]), NO_DISCOVERY
        )
    ).arc_json
    second = first_harvest(
        GeneralSchemaOrgMapper().map_graph(
            build(["https://example.org/alpha", "https://example.org/zeta"]), NO_DISCOVERY
        )
    ).arc_json
    assert '"@id":"URI=https://example.org/alpha"' in first
    assert '"@id":"URI=https://example.org/alpha"' in second
    assert root_identifier(first) == root_identifier(second) == "example_org_alpha"


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
        list(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY))


def test_named_property_value_with_doi_is_extracted() -> None:
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

    identifier = root_identifier(first_harvest(GeneralSchemaOrgMapper().map_graph(graph, NO_DISCOVERY)).arc_json)
    assert identifier == "10.1234/named-pv"


def test_multi_doi_with_source_url_uses_harvest_identifier_and_preserves_alternate() -> None:
    mapper = GeneralSchemaOrgMapper()
    source_url = "https://www.openagrar.de/receive/openagrar_mods_00107508"
    payload = dual_doi_payload("10.5281/zenodo.15672440", "10.3220/253-2025-54")
    harvested = first_harvest(
        mapper.map_graph(
            parse_jsonld(payload),
            MappingContext(
                source_url=source_url,
                harvest_source_id="openagrar_mods_00107508",
            ),
        )
    )
    assert root_identifier(harvested.arc_json) == "openagrar_mods_00107508"
    assert alternate_identifier_values(harvested.arc_json) == ["10.5281/zenodo.15672440"]
    assert "10.3220/253-2025-54" in harvested.arc_json


def test_multi_doi_harvest_identifier_stable_under_permuted_jsonld_order() -> None:
    mapper = GeneralSchemaOrgMapper()
    source_url = "https://www.openagrar.de/receive/openagrar_mods_00107508"
    first_payload = dual_doi_payload("10.5281/zenodo.15672440", "10.3220/253-2025-54")
    second_payload = dual_doi_payload("10.3220/253-2025-54", "10.5281/zenodo.15672440")
    ctx = MappingContext(source_url=source_url, harvest_source_id="openagrar_mods_00107508")
    first = root_identifier(first_harvest(mapper.map_graph(parse_jsonld(first_payload), ctx)).arc_json)
    second = root_identifier(first_harvest(mapper.map_graph(parse_jsonld(second_payload), ctx)).arc_json)
    assert first == second == "openagrar_mods_00107508"


def test_single_doi_without_source_url_has_no_alternate_identifier_comment() -> None:
    harvested = first_harvest(
        GeneralSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_PROPERTYVALUE_DOI), NO_DISCOVERY)
    )
    assert root_identifier(harvested.arc_json) == "10.3220/253-2025-42"
    assert not alternate_identifier_values(harvested.arc_json)


def test_shared_doi_on_two_pages_uses_distinct_harvest_identifiers() -> None:
    mapper = GeneralSchemaOrgMapper()
    graph = pangaea_doi_graph()
    url_a = "https://www.openagrar.de/receive/openagrar_mods_00088718"
    url_b = "https://www.openagrar.de/receive/openagrar_mods_00109919"
    id_a = root_identifier(
        first_harvest(
            mapper.map_graph(graph, MappingContext(source_url=url_a, harvest_source_id="openagrar_mods_00088718"))
        ).arc_json
    )
    id_b = root_identifier(
        first_harvest(
            mapper.map_graph(graph, MappingContext(source_url=url_b, harvest_source_id="openagrar_mods_00109919"))
        ).arc_json
    )
    assert id_a == "openagrar_mods_00088718"
    assert id_b == "openagrar_mods_00109919"
    assert id_a != id_b
    assert (
        "10.1594/PANGAEA.957630"
        in first_harvest(
            mapper.map_graph(graph, MappingContext(source_url=url_a, harvest_source_id="openagrar_mods_00088718"))
        ).arc_json
    )


def test_shared_doi_with_generic_source_url_uses_sanitized_page_url() -> None:
    mapper = GeneralSchemaOrgMapper()
    graph = pangaea_doi_graph()
    identifier = root_identifier(
        first_harvest(mapper.map_graph(graph, MappingContext(source_url="https://example.org/generic-page"))).arc_json
    )
    assert identifier == "example_org_generic-page"
    assert identifier != "10.1594/PANGAEA.957630"


def test_sorcering_pair_pages_keep_distinct_harvest_identifiers() -> None:
    mapper = GeneralSchemaOrgMapper()
    graph_a = parse_jsonld(
        """
        {
          "@context": "https://schema.org/",
          "@type": "Dataset",
          "name": "Sorcering A",
          "identifier": [{
            "@type": "PropertyValue",
            "propertyID": "https://registry.identifiers.org/registry/doi",
            "value": "10.1234/sorcering-a"
          }]
        }
        """
    )
    graph_b = parse_jsonld(
        """
        {
          "@context": "https://schema.org/",
          "@type": "Dataset",
          "name": "Sorcering B",
          "identifier": [{
            "@type": "PropertyValue",
            "propertyID": "https://registry.identifiers.org/registry/doi",
            "value": "10.1234/sorcering-b"
          }]
        }
        """
    )
    url_a = "https://www.openagrar.de/receive/openagrar_mods_00100605"
    url_b = "https://www.openagrar.de/receive/openagrar_mods_00108456"
    id_a = root_identifier(
        first_harvest(
            mapper.map_graph(graph_a, MappingContext(source_url=url_a, harvest_source_id="openagrar_mods_00100605"))
        ).arc_json
    )
    id_b = root_identifier(
        first_harvest(
            mapper.map_graph(graph_b, MappingContext(source_url=url_b, harvest_source_id="openagrar_mods_00108456"))
        ).arc_json
    )
    assert id_a == "openagrar_mods_00100605"
    assert id_b == "openagrar_mods_00108456"
    assert (
        "10.1234/sorcering-a"
        in first_harvest(
            mapper.map_graph(graph_a, MappingContext(source_url=url_a, harvest_source_id="openagrar_mods_00100605"))
        ).arc_json
    )
    assert (
        "10.1234/sorcering-b"
        in first_harvest(
            mapper.map_graph(graph_b, MappingContext(source_url=url_b, harvest_source_id="openagrar_mods_00108456"))
        ).arc_json
    )


def test_multi_dataset_page_uses_per_subject_ids_not_shared_harvest_source() -> None:
    """Page-level harvest context must not collide Investigation.identifier across Datasets."""
    schema = Namespace("https://schema.org/")
    graph = Graph()
    alpha = URIRef("https://example.org/dataset/alpha")
    beta = URIRef("https://example.org/dataset/beta")
    for subject, title in ((alpha, "Dataset Alpha"), (beta, "Dataset Beta")):
        graph.add((subject, RDF.type, schema.Dataset))
        graph.add((subject, schema.name, Literal(title)))

    harvested = list(
        GeneralSchemaOrgMapper().map_graph(
            graph,
            MappingContext(
                source_url="https://example.org/catalog/page",
                harvest_source_id="catalog_page_1",
            ),
        )
    )
    assert len(harvested) == 2
    identifiers = {root_identifier(item.arc_json) for item in harvested}
    assert identifiers == {"example_org_dataset_alpha", "example_org_dataset_beta"}
    assert "catalog_page_1" not in identifiers
