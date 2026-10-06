"""Unit tests for DCAT-AP → ARC mapper."""

from __future__ import annotations

import json

import pytest
from mapper_test_helpers import (
    NO_DISCOVERY,
    assert_harvest_has_no_bnode_labels,
    rocrate_prop,
    root_identifier,
    root_title,
)
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF

from middleware.payload.linked_data_mapper.ckanext_dcat_mapper import DCAT, FOAF, VCARD, CkanextDcatMapper

SUBJECT = URIRef("https://agrihub.example.org/dataset/0555406d")
_LOCN = Namespace("http://www.w3.org/ns/locn#")


def _mapper(catalog_name: str | None = None, catalog_url: str | None = None) -> CkanextDcatMapper:
    return CkanextDcatMapper(catalog_name=catalog_name, catalog_url=catalog_url)


def _mapped_arc_json(graph: Graph, mapper: CkanextDcatMapper | None = None) -> str:
    results = list((mapper or _mapper()).map_graph(graph, NO_DISCOVERY))
    assert len(results) == 1
    arc_json = results[0].arc_json
    assert_harvest_has_no_bnode_labels(arc_json)
    return arc_json


def _base_graph() -> Graph:
    graph = Graph()
    graph.add((SUBJECT, RDF.type, DCAT.Dataset))
    graph.add((SUBJECT, DCTERMS.title, Literal("Soil³ - Sustainable Subsoil Management")))
    graph.add((SUBJECT, DCTERMS.description, Literal("A subsoil management project")))
    graph.add((SUBJECT, DCTERMS.issued, Literal("2025-11-25T11:58:28")))
    return graph


def _comment_text(arc_json: str, name: str) -> str | None:
    payload = json.loads(arc_json)
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Comment" not in type_list:
            continue
        if rocrate_prop(item, "name") == name:
            return rocrate_prop(item, "text")
    return None


def test_ckanext_dcat_mapper_requires_a_dataset_subject() -> None:
    graph = Graph()
    graph.add((SUBJECT, DCTERMS.title, Literal("Not typed as dcat:Dataset")))
    with pytest.raises(ValueError, match="dcat:Dataset"):
        list(_mapper().map_graph(graph, NO_DISCOVERY))


def test_ckanext_dcat_mapper_missing_title_fails_closed_without_untitled() -> None:
    graph = Graph()
    graph.add((SUBJECT, RDF.type, DCAT.Dataset))
    with pytest.raises(ValueError, match="no usable dcterms:title"):
        list(_mapper().map_graph(graph, NO_DISCOVERY))


def test_ckanext_dcat_mapper_maps_core_fields() -> None:
    arc_json = _mapped_arc_json(_base_graph())
    assert root_title(arc_json) == "Soil³ - Sustainable Subsoil Management"
    assert root_identifier(arc_json)


def test_ckanext_dcat_mapper_identifier_uses_shared_sanitize() -> None:
    subject = URIRef("https://example.org/dataset/abc.123")
    graph = Graph()
    graph.add((subject, RDF.type, DCAT.Dataset))
    graph.add((subject, DCTERMS.title, Literal("Example")))

    harvested = list(_mapper().map_graph(graph, NO_DISCOVERY))[0]
    assert harvested.identifier == CkanextDcatMapper.sanitize_identifier(str(subject))


def test_ckanext_dcat_mapper_maps_keywords_and_language_comments() -> None:
    graph = _base_graph()
    graph.add((SUBJECT, DCAT.keyword, Literal("crop yield")))
    graph.add((SUBJECT, DCAT.keyword, Literal("nutrient efficiency")))
    graph.add((SUBJECT, DCTERMS.language, Literal("en")))

    arc_json = _mapped_arc_json(graph)
    keywords = _comment_text(arc_json, "Keywords")
    assert keywords is not None
    assert "crop yield" in keywords
    assert "nutrient efficiency" in keywords
    assert _comment_text(arc_json, "Language") == "en"


def test_ckanext_dcat_mapper_maps_publisher_org_name() -> None:
    graph = _base_graph()
    org = URIRef("https://agrihub.example.org/organization/1")
    graph.add((SUBJECT, DCTERMS.publisher, org))
    graph.add((org, FOAF.name, Literal("WZW - Lehrstuhl für Bodenkunde")))

    arc_json = _mapped_arc_json(graph)
    assert _comment_text(arc_json, "Publisher") == "WZW - Lehrstuhl für Bodenkunde"


def test_ckanext_dcat_mapper_unwraps_ckan_raw_json_contact_point() -> None:
    """ckanext-dcat sometimes serializes CKAN's raw maintainer JSON string as vcard:fn."""
    graph = _base_graph()
    contact = URIRef("https://agrihub.example.org/dataset/0555406d#contact")
    graph.add((SUBJECT, DCAT.contactPoint, contact))
    graph.add((
        contact,
        VCARD.fn,
        Literal('{"maintainer_name": "Merve Mentese", "maintainer_email": "hilal.mentese@tum.de"}'),
    ))

    arc_json = _mapped_arc_json(graph)
    contact_text = _comment_text(arc_json, "Contact Point")
    assert contact_text == "Merve Mentese <hilal.mentese@tum.de>"


def test_ckanext_dcat_mapper_unwraps_ckan_raw_json_array_publisher() -> None:
    """CKAN's raw ``author``/``maintainer`` package fields are single-element JSON arrays."""
    graph = _base_graph()
    org = URIRef("https://agrihub.example.org/organization/3")
    graph.add((SUBJECT, DCTERMS.publisher, org))
    graph.add((
        org,
        FOAF.name,
        Literal(
            '[{"maintainer_email": "david.gackstetter@tum.de", '
            '"maintainer_name": "David Gackstetter", "phone": "", "role": ""}]'
        ),
    ))

    arc_json = _mapped_arc_json(graph)
    assert _comment_text(arc_json, "Publisher") == "David Gackstetter <david.gackstetter@tum.de>"


def test_ckanext_dcat_mapper_falls_back_to_raw_text_for_unparseable_org_label() -> None:
    graph = _base_graph()
    org = URIRef("https://agrihub.example.org/organization/2")
    graph.add((SUBJECT, DCTERMS.publisher, org))
    graph.add((org, FOAF.name, Literal("{not valid json")))

    arc_json = _mapped_arc_json(graph)
    assert _comment_text(arc_json, "Publisher") == "{not valid json"


def test_ckanext_dcat_mapper_maps_distribution_table_details() -> None:
    graph = _base_graph()
    dist = URIRef("https://agrihub.example.org/dataset/0555406d/resource/a")
    graph.add((SUBJECT, DCAT.distribution, dist))
    graph.add((dist, RDF.type, DCAT.Distribution))
    graph.add((dist, DCTERMS.title, Literal("Project Information")))
    graph.add((dist, DCTERMS.format, Literal("HTML")))
    graph.add((dist, DCAT.accessURL, URIRef("https://example.org/soil3")))

    arc_json = _mapped_arc_json(graph)
    assert "Project Information" in arc_json
    assert "HTML" in arc_json
    assert "https://example.org/soil3" in arc_json


def test_ckanext_dcat_mapper_adds_catalog_comment_when_configured() -> None:
    arc_json = _mapped_arc_json(
        _base_graph(),
        mapper=_mapper(catalog_name="SRADI", catalog_url="https://agrihub.example.org"),
    )
    assert _comment_text(arc_json, "Data Catalog") == "SRADI (https://agrihub.example.org)"


def test_ckanext_dcat_mapper_omits_catalog_comment_when_unconfigured() -> None:
    arc_json = _mapped_arc_json(_base_graph())
    assert _comment_text(arc_json, "Data Catalog") is None


def test_ckanext_dcat_mapper_flags_spatial_extent_without_embedding_raw_geometry() -> None:
    graph = _base_graph()
    location = URIRef("https://agrihub.example.org/location/1")
    graph.add((SUBJECT, DCTERMS.spatial, location))
    huge_wkt = "MULTIPOLYGON(" + "(0 0, 1 1, 2 2)," * 500 + "(0 0, 1 1, 2 2))"
    graph.add((location, _LOCN.geometry, Literal(huge_wkt)))

    arc_json = _mapped_arc_json(graph)
    assert (
        _comment_text(arc_json, "Spatial Extent")
        == "Geographic extent provided by the source RDI (see the RDI record)."
    )
    assert huge_wkt not in arc_json
