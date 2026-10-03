"""Person ORCIDs in the Schema.org mapper (#405): from ``@id`` or ``identifier``, kept as ``Person.ORCID``."""

from __future__ import annotations

import json
from typing import Any

import pytest
from arctrl import ARC  # type: ignore[import-untyped]
from mapper_test_helpers import NO_DISCOVERY, first_harvest, parse_jsonld

from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper

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
    return first_harvest(GeneralSchemaOrgMapper().map_graph(parse_jsonld(payload), NO_DISCOVERY)).arc_json


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
