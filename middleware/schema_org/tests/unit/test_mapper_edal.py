"""EDAL Schema.org mapper unit tests."""

import json

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.schema_org.config import PayloadType
from middleware.schema_org.schema_org_mapper import EdalSchemaOrgMapper, SchemaOrgMapper

DCTERMS_CONFORMS_TO = URIRef("http://purl.org/dc/terms/conformsTo")


def _edal_graph() -> Graph:
    """Build an rdflib Graph resembling an e!DAL schema.org Dataset page."""
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("10.5447/ipk/2024/0")

    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("IPK genebank accessions passport data snapshot 2024-02-15")))
    graph.add((dataset, schema.description, Literal("This data set contains a snapshot of the passport data.")))
    graph.add((dataset, schema.license, Literal("https://creativecommons.org/licenses/by-sa/4.0/legalcode")))
    graph.add((dataset, schema.inLanguage, Literal("en")))
    keywords_str = "Passport data, genebank information, plant genetic ressources, IPK genebank, MCPD"
    graph.add((dataset, schema.keywords, Literal(keywords_str)))

    pub = URIRef("https://doi.ipk-gatersleben.de/publisher")
    graph.add((pub, RDF.type, schema.Organization))
    graph.add((pub, schema.name, Literal("e!DAL - PGP Repository, IPK Gatersleben")))
    graph.add((dataset, schema.publisher, pub))

    author = URIRef("https://orcid.org/0000-0002-3370-3218")
    graph.add((author, RDF.type, schema.Person))
    graph.add((author, schema.givenName, Literal("Markus")))
    graph.add((author, schema.familyName, Literal("Oppermann")))
    addr_str = "Leibniz Institute of Plant Genetics, Corrensstraße 3, 06466, Germany"
    graph.add((author, schema.address, Literal(addr_str)))
    graph.add((dataset, schema.author, author))

    creator = URIRef("https://orcid.org/0000-0002-3370-3218#creator")
    graph.add((creator, RDF.type, schema.Person))
    graph.add((creator, schema.name, Literal("Markus Oppermann")))
    graph.add((creator, schema.address, Literal(addr_str)))
    graph.add((dataset, schema.creator, creator))

    conforms = URIRef("https://bioschemas.org/profiles/Dataset/1.0-RELEASE")
    graph.add((dataset, DCTERMS_CONFORMS_TO, conforms))

    return graph


def _make_graph(name: str, identifier: str) -> Graph:
    """Build minimal schema.org Dataset graph."""
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef(identifier)
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal(name)))
    graph.add((dataset, schema.description, Literal("Test description")))
    return graph


def test_returns_valid_jsonld() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)

    parsed = json.loads(result)
    assert "@context" in parsed
    assert "@graph" in parsed


def test_investigation_identifier_from_doi() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    inv = next(n for n in parsed["@graph"] if n.get("@id") == "./")
    assert inv["identifier"] == "10.5447/ipk/2024/0"


def test_investigation_title_and_description() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    inv = next(n for n in parsed["@graph"] if n.get("@id") == "./")
    assert "IPK genebank accessions" in inv.get("name", "")
    assert "snapshot of the passport data" in inv.get("description", "")


def test_orcid_in_person_disambiguating_description() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    person = next(n for n in parsed["@graph"] if n.get("familyName") == "Oppermann")
    desc = person.get("disambiguatingDescription", "")
    assert "ORCID" in desc
    assert "0000-0002-3370-3218" in desc


def test_orcid_from_identifier_propertyvalue() -> None:
    """Author with ORCID as PropertyValue, not in @id."""
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("10.5447/ipk/2025/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Test Dataset")))
    graph.add((dataset, schema.description, Literal("Test description")))

    author = URIRef("https://example.org/person/1")
    graph.add((author, RDF.type, schema.Person))
    graph.add((author, schema.givenName, Literal("Jane")))
    graph.add((author, schema.familyName, Literal("Doe")))

    prov = URIRef("https://example.org/person/1/orcid")
    graph.add((prov, RDF.type, schema.PropertyValue))
    graph.add((prov, schema.propertyID, Literal("orcid")))
    graph.add((prov, schema.value, Literal("0000-0001-2345-6789")))
    graph.add((author, schema.identifier, prov))
    graph.add((dataset, schema.author, author))

    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    person = next(n for n in parsed["@graph"] if n.get("familyName") == "Doe")
    desc = person.get("disambiguatingDescription", "")
    assert "ORCID" in desc
    assert "0000-0001-2345-6789" in desc


def test_conforms_to_dc_namespace() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    comments = [n for n in parsed["@graph"] if n.get("@type") == "Comment"]
    assert any(n.get("name") == "Conforms To" and "bioschemas.org" in n.get("text", "") for n in comments)


def test_conforms_to_schema_namespace_fallback() -> None:
    """Fall back to schema:conformsTo when DC namespace absent."""
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("10.5447/ipk/2025/2")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Test Dataset")))
    graph.add((dataset, schema.description, Literal("Test")))
    graph.add((dataset, schema.conformsTo, Literal("https://some-standard.org/profile")))

    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    comments = [n for n in parsed["@graph"] if n.get("@type") == "Comment"]
    assert any(n.get("name") == "Conforms To" and "some-standard.org" in n.get("text", "") for n in comments)


def test_flat_string_address() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    persons = [n for n in parsed["@graph"] if n.get("familyName") == "Oppermann"]
    assert len(persons) >= 1
    found = False
    for p in persons:
        addr = p.get("address", "")
        if addr and "Corrensstraße" in str(addr):
            found = True
            break
    assert found


def test_keywords_comment() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    comments = [n for n in parsed["@graph"] if n.get("@type") == "Comment"]
    assert any(n.get("name") == "Keywords" and "Passport data" in n.get("text", "") for n in comments)


def test_license_and_language_comments() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    comments = [n for n in parsed["@graph"] if n.get("@type") == "Comment"]
    names = [n.get("name") for n in comments]
    assert "License" in names
    assert "Language" in names


def test_publisher_organization_contact() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)

    persons = [n for n in parsed["@graph"] if n.get("@type") == "Person"]
    publisher_person = next(
        (p for p in persons if "PGP" in p.get("familyName", "") or "PGP" in p.get("name", "")),
        None,
    )
    assert publisher_person is not None

    defined_terms = {n["@id"]: n.get("name") for n in parsed["@graph"] if n.get("@type") == "DefinedTerm"}
    job_title_id = publisher_person.get("jobTitle")
    if isinstance(job_title_id, dict):
        job_title_id = job_title_id.get("@id", "")
    assert defined_terms.get(job_title_id) == "publisher"


def test_publication_with_doi() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    articles = [n for n in parsed["@graph"] if n.get("@type") == "ScholarlyArticle"]
    assert len(articles) >= 1
    ids = [a.get("identifier") for a in articles]
    assert any("10.5447/ipk/2024/0" in str(i) for i in ids)


def test_contributor_mapped_as_person_with_role() -> None:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("10.5447/ipk/2025/3")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Contributor Test")))
    graph.add((dataset, schema.description, Literal("Test")))
    cont = URIRef("https://example.org/contributor/1")
    graph.add((cont, RDF.type, schema.Person))
    graph.add((cont, schema.givenName, Literal("Alice")))
    graph.add((cont, schema.familyName, Literal("Contributor")))
    graph.add((dataset, schema.contributor, cont))
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    persons = [n for n in parsed["@graph"] if n.get("@type") == "Person"]
    alice = next((p for p in persons if p.get("familyName") == "Contributor"), None)
    assert alice is not None
    assert alice.get("givenName") == "Alice"
    defined_terms = {n["@id"]: n.get("name") for n in parsed["@graph"] if n.get("@type") == "DefinedTerm"}
    role_id = alice.get("jobTitle")
    if isinstance(role_id, dict):
        role_id = role_id.get("@id", "")
    assert defined_terms.get(role_id) == "contributor"


def test_empty_contributor_skipped() -> None:
    graph = _edal_graph()
    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    defined_terms = [n for n in parsed["@graph"] if n.get("@type") == "DefinedTerm"]
    term_names = [t.get("name") for t in defined_terms]
    assert "contributor" not in term_names


def test_registered_by_payload_type() -> None:
    cls = SchemaOrgMapper.registry[PayloadType.edal]
    assert cls is EdalSchemaOrgMapper


def test_general_mapper_still_works() -> None:
    from middleware.schema_org.schema_org_mapper import GeneralSchemaOrgMapper

    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("General Dataset")))

    mapper = GeneralSchemaOrgMapper()
    result = mapper.map_graph(graph)
    assert result.startswith("{")


def test_empty_graph_raises_value_error() -> None:
    graph = Graph()
    mapper = EdalSchemaOrgMapper()
    raised = False
    try:
        mapper.map_graph(graph)
    except ValueError as e:
        raised = True
        assert "Graph does not contain" in str(e)
    assert raised


def test_iri_and_https_schema_both_handled() -> None:
    graph = Graph()
    schema = Namespace("http://schema.org/")
    dataset = URIRef("10.5447/ipk/2024/1")
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("HTTP Schema Dataset")))

    mapper = EdalSchemaOrgMapper()
    result = mapper.map_graph(graph)
    parsed = json.loads(result)
    inv = next(n for n in parsed["@graph"] if n.get("@id") == "./")
    assert "HTTP Schema Dataset" in inv.get("name", "")
