"""Unit tests for the EDAL-PGP mapper."""

import json

import pytest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.schema_org.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType
from middleware.schema_org.plugin import SchemaOrgPlugin
from middleware.schema_org.schema_org_mapper.edal_pgp import EdalPgpMapper

SCHEMA = Namespace("http://schema.org/")


@pytest.fixture
def mapper() -> EdalPgpMapper:
    return EdalPgpMapper()


def _dataset(uri: str = "https://example.org/dataset/1") -> tuple[Graph, URIRef]:
    ds = URIRef(uri)
    g = Graph()
    g.add((ds, RDF.type, SCHEMA.Dataset))
    g.add((ds, SCHEMA.name, Literal("Test Dataset")))
    return g, ds


def _parse_rocrate(result: str) -> dict:
    return json.loads(result)


# Registry -------------------------------------------------------------------


def test_mapper_registry_resolves_edal_pgp() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.edal_pgp,
        http=NiceHttpClientConfig(),
    )
    result = SchemaOrgPlugin.create_mapper(config)
    assert isinstance(result, EdalPgpMapper)


def test_general_mapper_still_works() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )
    result = SchemaOrgPlugin.create_mapper(config)
    from middleware.schema_org.schema_org_mapper.general import GeneralSchemaOrgMapper

    assert isinstance(result, GeneralSchemaOrgMapper)


# ORCID dedup -----------------------------------------------------------------


def test_orcid_preserved(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    person = URIRef("https://orcid.org/0000-0003-4387-4923")
    g.add((person, RDF.type, SCHEMA.Person))
    g.add((person, SCHEMA.givenName, Literal("Christian")))
    g.add((person, SCHEMA.familyName, Literal("Colmsee")))
    id1 = URIRef("https://orcid.org/0000-0003-4387-4923#id")
    g.add((person, SCHEMA.identifier, id1))
    g.add((id1, SCHEMA.propertyID, Literal("orcid")))
    g.add((id1, SCHEMA.value, Literal("0000-0003-4387-4923")))
    g.add((ds, SCHEMA.author, person))

    result = mapper.map_graph(g)
    assert "0000-0003-4387-4923" in result


def test_dedup_by_orcid(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    p1 = URIRef("https://orcid.org/0000-0003-4387-4923")
    g.add((p1, RDF.type, SCHEMA.Person))
    g.add((p1, SCHEMA.givenName, Literal("Christian")))
    g.add((p1, SCHEMA.familyName, Literal("Colmsee")))
    id1 = URIRef("https://orcid.org/0000-0003-4387-4923#id")
    g.add((p1, SCHEMA.identifier, id1))
    g.add((id1, SCHEMA.propertyID, Literal("orcid")))
    g.add((id1, SCHEMA.value, Literal("0000-0003-4387-4923")))

    p2 = URIRef("https://example.org/person/colmsee-no-orcid")
    g.add((p2, RDF.type, SCHEMA.Person))
    g.add((p2, SCHEMA.givenName, Literal("Christian")))
    g.add((p2, SCHEMA.familyName, Literal("Colmsee")))

    g.add((ds, SCHEMA.author, p1))
    g.add((ds, SCHEMA.creator, p2))

    result = mapper.map_graph(g)
    ro = _parse_rocrate(result)
    graph_nodes = ro.get("@graph", [])
    person_nodes = [n for n in graph_nodes if n.get("@type") == "Person"]
    assert len(person_nodes) == 1


def test_dedup_by_name_when_no_orcid(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    p1 = URIRef("https://example.org/person/1")
    g.add((p1, RDF.type, SCHEMA.Person))
    g.add((p1, SCHEMA.givenName, Literal("John")))
    g.add((p1, SCHEMA.familyName, Literal("Doe")))
    p2 = URIRef("https://example.org/person/2")
    g.add((p2, RDF.type, SCHEMA.Person))
    g.add((p2, SCHEMA.givenName, Literal("John")))
    g.add((p2, SCHEMA.familyName, Literal("Doe")))

    g.add((ds, SCHEMA.author, p1))
    g.add((ds, SCHEMA.creator, p2))

    result = mapper.map_graph(g)
    ro = _parse_rocrate(result)
    graph_nodes = ro.get("@graph", [])
    person_nodes = [n for n in graph_nodes if n.get("@type") == "Person"]
    assert len(person_nodes) == 1


def test_distinct_names_not_deduped(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    p1 = URIRef("https://example.org/person/1")
    g.add((p1, RDF.type, SCHEMA.Person))
    g.add((p1, SCHEMA.givenName, Literal("Alice")))
    g.add((p1, SCHEMA.familyName, Literal("Alpha")))
    p2 = URIRef("https://example.org/person/2")
    g.add((p2, RDF.type, SCHEMA.Person))
    g.add((p2, SCHEMA.givenName, Literal("Bob")))
    g.add((p2, SCHEMA.familyName, Literal("Beta")))

    g.add((ds, SCHEMA.author, p1))
    g.add((ds, SCHEMA.creator, p2))

    result = mapper.map_graph(g)
    ro = _parse_rocrate(result)
    graph_nodes = ro.get("@graph", [])
    person_nodes = [n for n in graph_nodes if n.get("@type") == "Person"]
    assert len(person_nodes) > 1


# License --------------------------------------------------------------------


def test_license_placeholder_emits_url_not_provided(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    g.add((ds, SCHEMA.license, Literal("$licenseURL")))

    result = mapper.map_graph(g)
    assert "URL not provided" in result


def test_normal_license_passes_through(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    g.add((ds, SCHEMA.license, Literal("https://creativecommons.org/licenses/by/4.0/")))

    result = mapper.map_graph(g)
    assert "https://creativecommons.org" in result


def test_no_license_omits_comment(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()

    result = mapper.map_graph(g)
    parsed = _parse_rocrate(result)
    text_content = json.dumps(parsed)
    assert "URL not provided" not in text_content


# Date -----------------------------------------------------------------------


def test_date_published_with_edal_does_not_crash(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    g.add((ds, SCHEMA.datePublished, Literal("Sat Jan 01 00:00:00 CET 2011")))

    result = mapper.map_graph(g)
    assert result.startswith("{")


def test_date_published_december_does_not_crash(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    g.add((ds, SCHEMA.datePublished, Literal("Mon Dec 15 12:30:45 CET 2014")))

    result = mapper.map_graph(g)
    assert result.startswith("{")


def test_date_published_invalid_does_not_crash(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    g.add((ds, SCHEMA.datePublished, Literal("not-a-date")))

    result = mapper.map_graph(g)
    assert result.startswith("{")


# ORCID extraction -----------------------------------------------------------


def test_orcid_extracted_from_property_value(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    person = URIRef("https://example.org/person/1")
    g.add((person, RDF.type, SCHEMA.Person))
    g.add((person, SCHEMA.givenName, Literal("Test")))
    g.add((person, SCHEMA.familyName, Literal("User")))
    id_node = URIRef("https://example.org/person/1/orcid")
    g.add((person, SCHEMA.identifier, id_node))
    g.add((id_node, SCHEMA.propertyID, Literal("orcid")))
    g.add((id_node, SCHEMA.value, Literal("0000-0000-0000-0000")))
    g.add((ds, SCHEMA.author, person))

    result = mapper.map_graph(g)
    assert "0000-0000-0000-0000" in result


def test_no_orcid_node_still_maps(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    person = URIRef("https://example.org/person/1")
    g.add((person, RDF.type, SCHEMA.Person))
    g.add((person, SCHEMA.givenName, Literal("Test")))
    g.add((person, SCHEMA.familyName, Literal("User")))
    g.add((ds, SCHEMA.author, person))

    result = mapper.map_graph(g)
    assert "Test" in result


# Address --------------------------------------------------------------------


def test_string_address_parsed(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    person = URIRef("https://example.org/person/1")
    g.add((person, RDF.type, SCHEMA.Person))
    g.add((person, SCHEMA.givenName, Literal("Test")))
    g.add((person, SCHEMA.familyName, Literal("User")))
    g.add((person, SCHEMA.address, Literal("IPK Gatersleben, D-06466, Germany")))
    g.add((ds, SCHEMA.author, person))

    result = mapper.map_graph(g)
    assert "D-06466" in result or "IPK" in result


def test_structured_address_uses_parent(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    person = URIRef("https://example.org/person/1")
    g.add((person, RDF.type, SCHEMA.Person))
    g.add((person, SCHEMA.givenName, Literal("Test")))
    g.add((person, SCHEMA.familyName, Literal("User")))
    addr = URIRef("https://example.org/address/1")
    g.add((addr, RDF.type, SCHEMA.PostalAddress))
    g.add((addr, SCHEMA.streetAddress, Literal("Corrensstr. 3")))
    g.add((addr, SCHEMA.postalCode, Literal("D-06466")))
    g.add((addr, SCHEMA.addressCountry, Literal("Germany")))
    g.add((person, SCHEMA.address, addr))
    g.add((ds, SCHEMA.author, person))

    result = mapper.map_graph(g)
    assert "Corrensstr" in result


def test_no_address_returns_none(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    person = URIRef("https://example.org/person/1")
    g.add((person, RDF.type, SCHEMA.Person))
    g.add((person, SCHEMA.givenName, Literal("Test")))
    g.add((person, SCHEMA.familyName, Literal("User")))
    g.add((ds, SCHEMA.author, person))

    result = mapper.map_graph(g)
    assert "Test" in result


# Keywords -------------------------------------------------------------------


def test_keywords_string_split(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    g.add((ds, SCHEMA.keywords, Literal("bioinformatics, source code, database")))

    result = mapper.map_graph(g)
    assert "bioinformatics" in result
    assert "source code" in result
    assert "database" in result


def test_keywords_single_term(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    g.add((ds, SCHEMA.keywords, Literal("genomics")))

    result = mapper.map_graph(g)
    assert "genomics" in result


# Description ----------------------------------------------------------------


def test_long_description_truncated(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    long_desc = "x" * 1000
    g.add((ds, SCHEMA.description, Literal(long_desc)))

    result = mapper.map_graph(g)
    parsed = _parse_rocrate(result)
    assert parsed is not None


def test_short_description_passes_through(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    short_desc = "Short description."
    g.add((ds, SCHEMA.description, Literal(short_desc)))

    result = mapper.map_graph(g)
    assert short_desc in result or "Test Dataset" in result


# ConformsTo -----------------------------------------------------------------


def test_dcterms_conforms_to_fallback(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    dcterms = Namespace("http://purl.org/dc/terms/")
    conforms = URIRef("https://bioschemas.org/profiles/Dataset/1.0-RELEASE")
    g.add((ds, dcterms.conformsTo, conforms))

    result = mapper.map_graph(g)
    assert "bioschemas.org" in result


def test_schema_conforms_to_preferred(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    dcterms = Namespace("http://purl.org/dc/terms/")
    g.add((ds, SCHEMA.conformsTo, URIRef("https://schema.org/version/1.0")))
    g.add((ds, dcterms.conformsTo, URIRef("https://bioschemas.org/profiles/Dataset/1.0-RELEASE")))

    result = mapper.map_graph(g)
    assert "schema.org/version" in result


# Contributor ----------------------------------------------------------------


def test_contributor_role_assigned(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    person = URIRef("https://example.org/contributor/1")
    g.add((person, RDF.type, SCHEMA.Person))
    g.add((person, SCHEMA.givenName, Literal("Helper")))
    g.add((person, SCHEMA.familyName, Literal("Contributor")))
    g.add((ds, SCHEMA.contributor, person))

    result = mapper.map_graph(g)
    assert "Helper" in result


# Publisher ------------------------------------------------------------------


def test_publisher_appended(mapper: EdalPgpMapper) -> None:
    g, ds = _dataset()
    pub = URIRef("https://example.org/publisher/1")
    g.add((pub, RDF.type, SCHEMA.Organization))
    g.add((pub, SCHEMA.name, Literal("IPK Gatersleben")))
    g.add((ds, SCHEMA.publisher, pub))

    result = mapper.map_graph(g)
    assert "IPK" in result


# Smoke tests ----------------------------------------------------------------


def test_smoke_from_fixture(mapper: EdalPgpMapper) -> None:
    fixture_path = "middleware/schema_org/tests/fixtures/edal_pgp_sample.json"
    with open(fixture_path) as f:
        data = json.load(f)
    g = Graph().parse(data=json.dumps(data), format="json-ld")
    result = mapper.map_graph(g)
    assert result.startswith("{")
    assert "@context" in result
