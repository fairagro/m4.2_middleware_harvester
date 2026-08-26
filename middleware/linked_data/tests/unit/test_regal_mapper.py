"""Unit tests for Regal → ARC mapper."""

from __future__ import annotations

import json
import re

import pytest
from mapper_test_helpers import NO_DISCOVERY, assert_harvest_has_no_bnode_labels
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF, SKOS

from middleware.linked_data.linked_data_mapper.regal_mapper import (
    DBO,
    REGAL,
    RESEARCH_DATA_TYPE,
    RegalMapper,
)

RESOURCE_BASE = "https://example.org/resource/"
SUBJECT = URIRef(f"{RESOURCE_BASE}frl:123")


def _mapper() -> RegalMapper:
    return RegalMapper(resource_base_url=RESOURCE_BASE)


def _mapped_arc_json(graph: Graph) -> str:
    """Map ``graph`` and assert the ARC JSON has no rdflib blank-node labels."""
    arc_json = _mapper().map_graph(graph, NO_DISCOVERY).arc_json
    assert_harvest_has_no_bnode_labels(arc_json)
    return arc_json


def _base_graph() -> Graph:
    graph = Graph()
    graph.add((SUBJECT, RDF.type, RESEARCH_DATA_TYPE))
    graph.add((SUBJECT, DCTERMS.title, Literal("Research Data Management Plan")))
    graph.add((SUBJECT, DCTERMS.description, Literal("A useful description")))
    graph.add((SUBJECT, REGAL.doi, Literal("10.4126/FRL01-0000123")))
    graph.add((SUBJECT, DCTERMS.issued, Literal("2024")))
    return graph


def test_regal_mapper_maps_orcid_comment_only_for_orcid_host() -> None:
    graph = _base_graph()
    orcid = URIRef("https://orcid.org/0000-0003-2547-933X")
    graph.add((SUBJECT, DCTERMS.creator, orcid))
    graph.add((orcid, SKOS.prefLabel, Literal("Fuerst, Julia")))

    text = json.dumps(json.loads(_mapped_arc_json(graph)))
    assert "https://orcid.org/0000-0003-2547-933X" in text


def test_regal_mapper_ignores_lookalike_orcid_host() -> None:
    graph = _base_graph()
    fake = URIRef("https://evil-orcid.org/0000-0003-2547-933X")
    graph.add((SUBJECT, DCTERMS.creator, fake))
    graph.add((fake, SKOS.prefLabel, Literal("Fuerst, Julia")))

    text = json.dumps(json.loads(_mapped_arc_json(graph)))
    assert "Fuerst" in text
    assert "evil-orcid.org" not in text


def test_regal_mapper_maps_core_fields() -> None:
    graph = _base_graph()
    creator = URIRef("https://orcid.org/0000-0003-2547-933X")
    graph.add((SUBJECT, DCTERMS.creator, creator))
    graph.add((creator, SKOS.prefLabel, Literal("Fuerst, Julia")))

    institution = URIRef("https://d-nb.info/gnd/1246206420")
    graph.add((SUBJECT, DBO.institution, institution))
    graph.add((institution, SKOS.prefLabel, Literal("NFDI4Health")))

    license_node = URIRef("https://creativecommons.org/licenses/by/4.0/")
    graph.add((SUBJECT, REGAL.license, license_node))

    part = URIRef(f"{RESOURCE_BASE}frl:file1")
    graph.add((SUBJECT, DCTERMS.hasPart, part))
    graph.add((part, SKOS.prefLabel, Literal("readme.txt")))

    result = json.loads(_mapped_arc_json(graph))
    assert "@graph" in result
    text = json.dumps(result)
    assert "Research Data Management Plan" in text
    assert "10.4126/FRL01-0000123" in text
    assert "Fuerst" in text
    assert "readme.txt" in text
    assert f"{RESOURCE_BASE}frl:file1" in text
    assert f"{RESOURCE_BASE}{RESOURCE_BASE}" not in text
    assert "https:%2F%2F" not in text


def test_regal_mapper_expands_compact_has_part_id() -> None:
    graph = _base_graph()
    part = URIRef("frl:file-compact")
    graph.add((SUBJECT, DCTERMS.hasPart, part))
    graph.add((part, SKOS.prefLabel, Literal("data.csv")))

    text = json.dumps(json.loads(_mapped_arc_json(graph)))
    assert f"{RESOURCE_BASE}frl:file-compact" in text
    assert "data.csv" in text


def test_regal_mapper_requires_research_data_type() -> None:
    graph = Graph()
    graph.add((SUBJECT, DCTERMS.title, Literal("Not research data")))
    with pytest.raises(ValueError, match="ResearchData"):
        _mapper().map_graph(graph, NO_DISCOVERY)


def test_regal_mapper_requires_identity() -> None:
    graph = Graph()
    subject = URIRef("https://example.org/unknown-record")
    graph.add((subject, RDF.type, RESEARCH_DATA_TYPE))
    graph.add((subject, DCTERMS.title, Literal("No id")))
    with pytest.raises(ValueError, match="missing both @id and doi"):
        _mapper().map_graph(graph, NO_DISCOVERY)


def test_regal_mapper_creates_spatial_sampling_when_location_present() -> None:
    graph = _base_graph()
    place = URIRef("https://example.org/place/1")
    graph.add((SUBJECT, REGAL.recordingLocation, place))
    graph.add((place, SKOS.prefLabel, Literal("Cologne")))

    result = json.loads(_mapped_arc_json(graph))
    text = json.dumps(result)
    assert "Spatial Sampling" in text
    assert "Cologne" in text


def test_regal_mapper_prefers_joined_funding() -> None:
    graph = _base_graph()
    joined = URIRef("https://example.org/funding/1")
    funder = URIRef("http://dx.doi.org/10.13039/501100001659")
    graph.add((SUBJECT, URIRef("info:regal/regal/joinedFunding"), joined))
    graph.add((joined, REGAL.fundingProgramJoined, Literal("NFDI4Health Consortium")))
    graph.add((joined, REGAL.projectIdJoined, Literal("442326535")))
    graph.add((joined, REGAL.fundingJoined, funder))
    graph.add((funder, SKOS.prefLabel, Literal("Deutsche Forschungsgemeinschaft")))
    # Flat duplicates should be ignored when joinedFunding exists.
    graph.add((SUBJECT, REGAL.fundingProgram, Literal("ignored-flat-program")))

    result = json.loads(_mapped_arc_json(graph))
    text = json.dumps(result)
    assert "NFDI4Health Consortium" in text
    assert "442326535" in text
    assert "Deutsche Forschungsgemeinschaft" in text
    assert "ignored-flat-program" not in text


def test_regal_mapper_skips_opaque_duplicates_for_dedicated_predicates() -> None:
    graph = _base_graph()
    graph.add((SUBJECT, REGAL.catalogId, Literal("cat-42")))
    item = URIRef("https://example.org/oai/1")
    graph.add((SUBJECT, REGAL.itemID, item))
    graph.add((item, SKOS.prefLabel, Literal("oai:frl.publisso.de:frl:123")))
    graph.add((SUBJECT, REGAL.associatedPublication, URIRef("https://doi.org/10.1000/xyz")))

    text = json.dumps(json.loads(_mapped_arc_json(graph)))
    assert "Catalog ID" in text
    assert "cat-42" in text
    assert "OAI Identifier" in text
    assert "oai:frl.publisso.de:frl:123" in text
    assert "Associated Publication" in text
    assert "https://doi.org/10.1000/xyz" in text
    # Opaque fallback would emit the raw local names as comment names.
    assert '"catalogId"' not in text
    assert '"itemID"' not in text
    assert '"associatedPublication"' not in text


def test_regal_mapper_license_blank_node_uses_pref_label() -> None:
    graph = _base_graph()
    license_node = BNode()
    graph.add((SUBJECT, REGAL.license, license_node))
    graph.add((license_node, SKOS.prefLabel, Literal("CC BY 4.0")))

    text = json.dumps(json.loads(_mapped_arc_json(graph)))
    assert "CC BY 4.0" in text
    assert "_:" not in text


def test_regal_mapper_org_style_pref_label_is_comment_not_empty_given_person() -> None:
    graph = _base_graph()
    org = URIRef("https://example.org/org/zenodo")
    graph.add((SUBJECT, DCTERMS.creator, org))
    graph.add((org, SKOS.prefLabel, Literal("Zenodo")))

    person = URIRef("https://orcid.org/0000-0003-2547-933X")
    graph.add((SUBJECT, DCTERMS.creator, person))
    graph.add((person, SKOS.prefLabel, Literal("Fuerst, Julia")))

    text = json.dumps(json.loads(_mapped_arc_json(graph)))
    assert "Fuerst" in text
    assert "Julia" in text
    assert "Zenodo" in text
    payload = json.loads(text)
    people = [
        item
        for item in payload["@graph"]
        if item.get("@type") == "Person" or (isinstance(item.get("@type"), list) and "Person" in item.get("@type", []))
    ]
    assert all(str(p.get("givenName", "")).strip() for p in people)
    assert not any(p.get("familyName") == "Zenodo" for p in people)


def test_regal_mapper_multiword_org_pref_label_without_comma_is_comment() -> None:
    """Regal has no Family, Given → Comment; do not nameparse into a fake Person."""
    graph = _base_graph()
    org = URIRef("https://example.org/org/nfdi4health-tf")
    graph.add((SUBJECT, DCTERMS.creator, org))
    graph.add((org, SKOS.prefLabel, Literal("NFDI4Health Task Force COVID-19")))

    arc_json = _mapped_arc_json(graph)
    entries = {(name, text) for name, text in _comment_entries(arc_json)}
    assert ("Creator", "NFDI4Health Task Force COVID-19 (https://example.org/org/nfdi4health-tf)") in entries
    payload = json.loads(arc_json)
    people = [
        item
        for item in payload["@graph"]
        if item.get("@type") == "Person" or (isinstance(item.get("@type"), list) and "Person" in item.get("@type", []))
    ]
    assert not any("NFDI4Health" in str(p.get("familyName", "")) for p in people)
    assert not any("Task" in str(p.get("givenName", "")) for p in people)


def test_regal_mapper_org_style_bnode_pref_label_comment_omits_bnode_id() -> None:
    graph = _base_graph()
    org = BNode()
    graph.add((SUBJECT, DCTERMS.creator, org))
    graph.add((org, SKOS.prefLabel, Literal("Zenodo")))

    arc_json = _mapped_arc_json(graph)
    entries = {(name, text) for name, text in _comment_entries(arc_json) if name != "@id"}
    assert ("Creator", "Zenodo") in entries
    assert not any("Zenodo (" in text for _, text in entries)
    assert _BLANK_NODE_LABEL.search(json.dumps(json.loads(arc_json))) is None


def test_regal_mapper_orcid_without_given_name_fails_closed() -> None:
    graph = _base_graph()
    orcid = URIRef("https://orcid.org/0000-0003-2547-933X")
    graph.add((SUBJECT, DCTERMS.creator, orcid))
    graph.add((orcid, SKOS.prefLabel, Literal("OnlyFamily")))

    with pytest.raises(ValueError, match="non-empty given name"):
        _mapper().map_graph(graph, NO_DISCOVERY)


_BLANK_NODE_LABEL = re.compile(r"(?:N[0-9a-f]{32}|_:[A-Za-z0-9]+)", re.IGNORECASE)


def _comment_entries(arc_json: str) -> list[tuple[str, str]]:
    """Return (name, text) pairs for Investigation-style Comment nodes in RO-Crate JSON."""
    assert_harvest_has_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    entries: list[tuple[str, str]] = []
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Comment" not in type_list:
            continue
        name = str(item.get("name") or item.get("http://schema.org/name") or "")
        text = str(item.get("text") or item.get("http://schema.org/text") or "")
        entries.append((name, text))
        # Also catch blank-node labels that land in @id.
        comment_id = str(item.get("@id") or "")
        if comment_id:
            entries.append(("@id", comment_id))
    return entries


def test_contributor_order_blank_node_does_not_create_comment() -> None:
    graph = _base_graph()
    order_node = BNode()
    graph.add((SUBJECT, REGAL.contributorOrder, order_node))

    arc_json = _mapped_arc_json(graph)
    entries = _comment_entries(arc_json)
    assert not any(name == "contributorOrder" for name, _ in entries)
    blob = json.dumps(json.loads(arc_json))
    assert _BLANK_NODE_LABEL.search(blob) is None
    assert "contributorOrder" not in blob


def test_contributor_order_blank_nodes_stable_across_two_maps() -> None:
    def build() -> Graph:
        graph = _base_graph()
        graph.add((SUBJECT, REGAL.contributorOrder, BNode()))
        return graph

    first = _comment_entries(_mapped_arc_json(build()))
    second = _comment_entries(_mapped_arc_json(build()))
    first_set = {(n, t) for n, t in first if n != "@id"}
    second_set = {(n, t) for n, t in second if n != "@id"}
    assert first_set == second_set
    assert not any(n == "contributorOrder" for n, _ in first_set)


def test_opaque_unknown_predicate_unlabelled_blank_node_is_skipped() -> None:
    graph = _base_graph()
    unknown = URIRef("http://hbz-nrw.de/regal#emi_measurement_techniques")
    graph.add((SUBJECT, unknown, BNode()))

    entries = _comment_entries(_mapped_arc_json(graph))
    assert not any(name == "emi_measurement_techniques" for name, _ in entries)
    blob = json.dumps(json.loads(_mapped_arc_json(graph)))
    assert _BLANK_NODE_LABEL.search(blob) is None


def test_opaque_blank_node_with_pref_label_is_kept() -> None:
    graph = _base_graph()
    unknown = URIRef("http://hbz-nrw.de/regal#emi_measurement_techniques")
    node = BNode()
    graph.add((SUBJECT, unknown, node))
    graph.add((node, SKOS.prefLabel, Literal("Stable Label")))

    entries = _comment_entries(_mapped_arc_json(graph))
    assert ("emi_measurement_techniques", "Stable Label") in {(n, t) for n, t in entries if n != "@id"}
    blob = json.dumps(json.loads(_mapped_arc_json(graph)))
    assert _BLANK_NODE_LABEL.search(blob) is None
