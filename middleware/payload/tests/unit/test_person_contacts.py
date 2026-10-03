"""Unit tests for shared Person contact helpers."""

from __future__ import annotations

import pytest
from arctrl import ArcInvestigation, OntologyAnnotation, Person  # type: ignore[import-untyped]

from middleware.payload.person_contacts import add_contact, orcid_id, publication_authors


def _investigation(*contacts: tuple[str, str, str]) -> ArcInvestigation:
    inv = ArcInvestigation.create(identifier="inv", title="Title")
    for last, first, role in contacts:
        person = Person.create(last_name=last, first_name=first)
        person.Roles.append(OntologyAnnotation(name=role))
        inv.Contacts.append(person)
    return inv


def test_publication_authors_initial_space_last_in_contact_order() -> None:
    inv = _investigation(("Zebra", "Zoe", "author"), ("Lovelace", "Ada", "author"))
    assert publication_authors(inv) == "Z. Zebra; A. Lovelace"


def test_publication_authors_role_match_is_case_insensitive() -> None:
    inv = _investigation(("Doe", "John", "Author"), ("Roe", "Rita", "contributor"))
    assert publication_authors(inv) == "J. Doe"


def test_publication_authors_single_name_part_and_no_commas() -> None:
    inv = _investigation(("Doe", "", "author"), ("", "Rita", "author"))
    assert publication_authors(inv) == "Doe; Rita"


def test_publication_authors_none_without_authors() -> None:
    assert publication_authors(_investigation(("Roe", "Rita", "publisher"))) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0000-0002-1825-0097", "0000-0002-1825-0097"),
        (" https://orcid.org/0000-0002-1825-0097/ ", "0000-0002-1825-0097"),
        ("http://www.orcid.org/0000-0002-4316-078x", "0000-0002-4316-078X"),
        ("https://orcid.org/0000-0002-1825-009", None),
        ("https://evil-orcid.org/0000-0002-1825-0097", None),
        ("https://sandbox.orcid.org/0000-0002-1825-0097", None),
        ("", None),
        (None, None),
    ],
)
def test_orcid_id(value: str | None, expected: str | None) -> None:
    assert orcid_id(value) == expected


def test_add_contact_merges_roles_by_orcid() -> None:
    inv = ArcInvestigation.create(identifier="inv", title="Title")
    add_contact(inv, Person.create(orcid="0000-0002-1825-0097", last_name="Doe", first_name="John"), "author")
    add_contact(inv, Person.create(orcid="0000-0002-1825-0097", last_name="Doe", first_name="J."), "contributor")
    add_contact(inv, Person.create(orcid="0000-0002-1825-0097", last_name="Doe", first_name="John"), "Author")
    add_contact(inv, Person.create(last_name="Roe", first_name="Rita"), "author")
    add_contact(inv, Person.create(last_name="Roe", first_name="Rita"), "author")

    assert [(c.LastName, [r.Name for r in c.Roles]) for c in inv.Contacts] == [
        ("Doe", ["author", "contributor"]),
        ("Roe", ["author"]),
        ("Roe", ["author"]),
    ]


def test_add_contact_match_name_merges_and_fills_orcid() -> None:
    inv = ArcInvestigation.create(identifier="inv", title="Title")
    add_contact(inv, Person.create(last_name="Doe", first_name="John"), "author", match_name=True)
    add_contact(
        inv,
        Person.create(orcid="0000-0002-1825-0097", last_name="doe", first_name="John "),
        "contributor",
        match_name=True,
    )
    add_contact(
        inv, Person.create(orcid="0000-0002-4316-078X", last_name="Doe", first_name="John"), "author", match_name=True
    )
    add_contact(inv, Person.create(last_name="Doe", first_name="John"), "author")

    assert [(c.ORCID, [r.Name for r in c.Roles]) for c in inv.Contacts] == [
        ("0000-0002-1825-0097", ["author", "contributor"]),
        ("0000-0002-4316-078X", ["author"]),
        (None, ["author"]),
    ]
