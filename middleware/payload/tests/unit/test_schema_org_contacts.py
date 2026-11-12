"""Schema.org mapper contacts: ORCIDs as ``Person.ORCID`` (#405), one contact per person (#406)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from arctrl import ARC  # type: ignore[import-untyped]
from mapper_test_helpers import NO_DISCOVERY, first_harvest, parse_jsonld
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.placeholders import PlaceholderConfig

COLMSEE = "0000-0003-4387-4923"
LANGE = "0000-0002-4316-078X"


def _dataset(**persons: list[dict[str, Any]]) -> str:
    return json.dumps({
        "@context": {"@vocab": "https://schema.org/"},
        "@id": "https://doi.org/10.5447/ipk/2011/0",
        "@type": "Dataset",
        "name": "e!DAL dataset",
        **persons,
    })


def _person(given: str, family: str, **extra: Any) -> dict[str, Any]:
    return {"@type": "Person", "givenName": given, "familyName": family, "name": f"{given} {family}", **extra}


def _edal_person(given: str, family: str, orcid: str) -> dict[str, Any]:
    """Person shape of e!DAL landing pages (``@id`` plus ``identifier`` PropertyValue)."""
    return _person(
        given,
        family,
        **{
            "@id": f"https://orcid.org/{orcid}",
            "identifier": {"@type": "PropertyValue", "propertyID": "orcid", "value": orcid},
        },
    )


def _map(payload: str) -> str:
    return first_harvest(
        GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(parse_jsonld(payload), NO_DISCOVERY)
    ).arc_json


def _contacts(arc_json: str) -> list[tuple[str, str | None, list[str]]]:
    """``(family, ORCID, roles)`` per contact, read back through ARCtrl like the API does."""
    arc = ARC.from_rocrate_json_string(arc_json)
    return [(c.LastName, c.ORCID, [r.Name for r in c.Roles]) for c in arc.Contacts]


def test_edal_author_orcid_becomes_person_id() -> None:
    arc_json = _map(
        _dataset(
            author=[
                _edal_person("Christian", "Colmsee", COLMSEE),
                _person("Steffen", "Flemming"),
                _edal_person("Matthias", "Lange", LANGE),
            ]
        )
    )

    assert sorted(_contacts(arc_json)) == [
        ("Colmsee", COLMSEE, ["author"]),
        ("Flemming", None, ["author"]),
        ("Lange", LANGE, ["author"]),
    ]
    person_ids = {n["familyName"]: n["@id"] for n in json.loads(arc_json)["@graph"] if "jobTitle" in n}
    assert person_ids["Colmsee"] == f"http://orcid.org/{COLMSEE}"
    assert person_ids["Flemming"].startswith("#Person_")


@pytest.mark.parametrize(
    "identifier",
    [
        COLMSEE,
        f"https://orcid.org/{COLMSEE}",
        {"@id": f"https://orcid.org/{COLMSEE}"},
        {"@type": "PropertyValue", "propertyID": "ORCID", "value": COLMSEE},
        {"@type": "PropertyValue", "propertyID": "https://registry.identifiers.org/registry/orcid", "value": COLMSEE},
        {"@type": "PropertyValue", "value": f"https://orcid.org/{COLMSEE}"},
    ],
)
def test_orcid_from_identifier_without_person_id(identifier: object) -> None:
    arc_json = _map(_dataset(author=[_person("Christian", "Colmsee", identifier=identifier)]))
    assert _contacts(arc_json) == [("Colmsee", COLMSEE, ["author"])]


@pytest.mark.parametrize(
    "extra",
    [
        {"@id": "https://example.org/people/colmsee"},
        {"@id": "https://evil-orcid.org/0000-0003-4387-4923"},
        {"identifier": {"@type": "PropertyValue", "propertyID": "isni", "value": COLMSEE}},
        {"identifier": "0000-0003-4387-492"},
    ],
)
def test_non_orcid_identifiers_are_not_orcids(extra: dict[str, Any]) -> None:
    arc_json = _map(_dataset(author=[_person("Christian", "Colmsee", **extra)]))
    assert _contacts(arc_json) == [("Colmsee", None, ["author"])]


def test_creator_without_orcid_and_author_with_orcid_merge_keeping_orcid() -> None:
    arc_json = _map(
        _dataset(
            creator=[_person("Christian", "Colmsee")],
            author=[_edal_person("Christian", "Colmsee", COLMSEE)],
        )
    )
    assert _contacts(arc_json) == [("Colmsee", COLMSEE, ["author"])]


def test_same_orcid_as_author_and_contributor_is_one_contact() -> None:
    arc_json = _map(
        _dataset(
            author=[_edal_person("Christian", "Colmsee", COLMSEE)],
            contributor=[_edal_person("Christian", "Colmsee", COLMSEE)],
        )
    )
    assert _contacts(arc_json) == [("Colmsee", COLMSEE, ["author", "contributor"])]


def _edal_2011_0() -> str:
    """Shape of 10.5447/ipk/2011/0: ``author`` = creators (some with ORCID) + contributors."""
    creators = [
        _person("Christian", "Colmsee"),
        _person("Steffen", "Flemming"),
        _person("Matthias", "Klapperstück"),
        _person("Matthias", "Lange"),
        _person("Uwe", "Scholz"),
    ]
    contributors = [
        _person("Christian", "Friedrich"),
        _person("Burkhard", "Steuernagel"),
        _person("Stephan", "Weise"),
    ]
    authors = [
        _edal_person("Christian", "Colmsee", COLMSEE),
        _person("Steffen", "Flemming"),
        _person("Matthias", "Klapperstück"),
        _edal_person("Matthias", "Lange", LANGE),
        _person("Uwe", "Scholz"),
        *contributors,
    ]
    return _dataset(creator=creators, author=authors, contributor=[{**c} for c in contributors])


def test_edal_authors_and_contributors_are_one_contact_per_person() -> None:
    contacts = _contacts(_map(_edal_2011_0()))

    assert len(contacts) == 8
    assert sorted(contacts) == [
        ("Colmsee", COLMSEE, ["author"]),
        ("Flemming", None, ["author"]),
        ("Friedrich", None, ["author", "contributor"]),
        ("Klapperstück", None, ["author"]),
        ("Lange", LANGE, ["author"]),
        ("Scholz", None, ["author"]),
        ("Steuernagel", None, ["author", "contributor"]),
        ("Weise", None, ["author", "contributor"]),
    ]


def test_contributor_only_keeps_contributor_role() -> None:
    contacts = _contacts(
        _map(_dataset(author=[_person("Christian", "Colmsee")], contributor=[_person("Stephan", "Weise")]))
    )
    assert contacts == [("Colmsee", None, ["author"]), ("Weise", None, ["contributor"])]


def test_same_name_different_orcids_stay_two_contacts() -> None:
    contacts = _contacts(
        _map(
            _dataset(
                author=[_edal_person("Christian", "Colmsee", COLMSEE)],
                contributor=[_edal_person("Christian", "Colmsee", LANGE)],
            )
        )
    )
    assert sorted(contacts) == [("Colmsee", LANGE, ["contributor"]), ("Colmsee", COLMSEE, ["author"])]


def test_publication_authors_list_each_person_once() -> None:
    arc = ARC.from_rocrate_json_string(_map(_edal_2011_0()))
    authors = arc.Publications[0].Authors.split("; ")
    assert len(authors) == len(set(authors)) == 8


def test_organisation_creator_is_one_creator_organization_comment() -> None:
    """e!DAL 10.5447/ipk/2016/12: the ``IBSC`` Organization is both creator and author (#411)."""
    ibsc = {"@type": "Organization", "name": "IBSC", "url": "https://www.barleygenome.org/"}
    arc_json = _map(
        _dataset(
            creator=[ibsc],
            author=[ibsc],
            contributor=[{"@type": "Organization", "name": "IPK Gatersleben"}],
        )
    )

    arc = ARC.from_rocrate_json_string(arc_json)
    assert not list(arc.Contacts)
    assert [(c.Name, c.Value) for c in arc.Comments if c.Name.startswith(("Creator", "Contributor"))] == [
        ("Creator Organization", "IBSC"),
        ("Creator Organization URL", "https://www.barleygenome.org/"),
        ("Contributor", "IPK Gatersleben"),
    ]


# --- flat / structured address affiliation (#414) ---------------------------


_EDAL_ADDRESS = (
    "Leibniz Institute of Plant Genetics and Crop Plant Research (IPK), Seeland OT Gatersleben, "
    "Corrensstraße 3, D-06466, Germany"
)


def _person_graph(address: Literal | BNode | None, affiliation: str | None = None) -> tuple[Graph, BNode]:
    graph = Graph()
    schema = Namespace("https://schema.org/")
    dataset = URIRef("https://example.org/dataset/address")
    person = BNode()
    graph.add((dataset, RDF.type, schema.Dataset))
    graph.add((dataset, schema.name, Literal("Addressed")))
    graph.add((dataset, schema.creator, person))
    graph.add((person, RDF.type, schema.Person))
    graph.add((person, schema.givenName, Literal("Markus")))
    graph.add((person, schema.familyName, Literal("Oppermann")))
    if address is not None:
        graph.add((person, schema.address, address))
    if affiliation is not None:
        org = BNode()
        graph.add((person, schema.affiliation, org))
        graph.add((org, RDF.type, schema.Organization))
        graph.add((org, schema.name, Literal(affiliation)))
    return graph, person


def _person_address_and_affiliation(graph: Graph) -> tuple[object, object]:
    payload = json.loads(
        first_harvest(GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(graph, NO_DISCOVERY)).arc_json
    )
    nodes = {item.get("@id"): item for item in payload["@graph"]}
    person = next(item for item in payload["@graph"] if item.get("familyName") == "Oppermann")
    org_ref = person.get("affiliation") or {}
    org_name = nodes.get(org_ref.get("@id"), {}).get("name") if isinstance(org_ref, dict) else None
    return person.get("address"), org_name or None


def test_flat_address_first_segment_is_affiliation_fallback() -> None:
    """e!DAL gives no affiliation and a flat address starting with the institute (#414)."""
    graph, _ = _person_graph(Literal(_EDAL_ADDRESS))

    address, affiliation = _person_address_and_affiliation(graph)

    assert affiliation == "Leibniz Institute of Plant Genetics and Crop Plant Research (IPK)"
    assert address == _EDAL_ADDRESS


def test_explicit_affiliation_wins_over_flat_address() -> None:
    graph, _ = _person_graph(Literal(_EDAL_ADDRESS), affiliation="Thünen Institute")

    assert _person_address_and_affiliation(graph)[1] == "Thünen Institute"


@pytest.mark.parametrize(
    ("address", "expected_affiliation"),
    [
        (", Department of Landscape Ecology, Kiel University, Germany", "Department of Landscape Ecology"),
        (" ,  , ", None),
    ],
)
def test_flat_address_skips_empty_segments(address: str, expected_affiliation: str | None) -> None:
    graph, _ = _person_graph(Literal(address))

    result_address, affiliation = _person_address_and_affiliation(graph)

    assert affiliation == expected_affiliation
    if expected_affiliation is None:
        assert result_address is None


def test_structured_address_keeps_locality_and_gives_no_affiliation() -> None:
    schema = Namespace("https://schema.org/")
    postal = BNode()
    graph, _ = _person_graph(postal)
    graph.add((postal, RDF.type, schema.PostalAddress))
    graph.add((postal, schema.streetAddress, Literal("Corrensstraße 3")))
    graph.add((postal, schema.postalCode, Literal("06466")))
    graph.add((postal, schema.addressLocality, Literal("Seeland OT Gatersleben")))
    graph.add((postal, schema.addressCountry, Literal("Germany")))

    address, affiliation = _person_address_and_affiliation(graph)

    assert address == "Corrensstraße 3, 06466, Seeland OT Gatersleben, Germany"
    assert affiliation is None
