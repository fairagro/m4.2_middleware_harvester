"""Unit tests for Regal → ARC mapper."""

from __future__ import annotations

import json

import pytest
from rdflib import Graph, Literal, URIRef
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

    text = json.dumps(json.loads(_mapper().map_graph(graph)))
    assert "https://orcid.org/0000-0003-2547-933X" in text


def test_regal_mapper_ignores_lookalike_orcid_host() -> None:
    graph = _base_graph()
    fake = URIRef("https://evil-orcid.org/0000-0003-2547-933X")
    graph.add((SUBJECT, DCTERMS.creator, fake))
    graph.add((fake, SKOS.prefLabel, Literal("Fuerst, Julia")))

    text = json.dumps(json.loads(_mapper().map_graph(graph)))
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

    result = json.loads(_mapper().map_graph(graph))
    assert "@graph" in result
    text = json.dumps(result)
    assert "Research Data Management Plan" in text
    assert "10.4126/FRL01-0000123" in text
    assert "Fuerst" in text
    assert "readme.txt" in text


def test_regal_mapper_requires_research_data_type() -> None:
    graph = Graph()
    graph.add((SUBJECT, DCTERMS.title, Literal("Not research data")))
    with pytest.raises(ValueError, match="ResearchData"):
        _mapper().map_graph(graph)


def test_regal_mapper_requires_identity() -> None:
    graph = Graph()
    subject = URIRef("https://example.org/unknown-record")
    graph.add((subject, RDF.type, RESEARCH_DATA_TYPE))
    graph.add((subject, DCTERMS.title, Literal("No id")))
    with pytest.raises(ValueError, match="missing both @id and doi"):
        _mapper().map_graph(graph)


def test_regal_mapper_creates_spatial_sampling_when_location_present() -> None:
    graph = _base_graph()
    place = URIRef("https://example.org/place/1")
    graph.add((SUBJECT, REGAL.recordingLocation, place))
    graph.add((place, SKOS.prefLabel, Literal("Cologne")))

    result = json.loads(_mapper().map_graph(graph))
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

    result = json.loads(_mapper().map_graph(graph))
    text = json.dumps(result)
    assert "NFDI4Health Consortium" in text
    assert "442326535" in text
    assert "Deutsche Forschungsgemeinschaft" in text
    assert "ignored-flat-program" not in text
