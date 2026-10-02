"""Unit tests for shared Person contact helpers."""

from __future__ import annotations

from arctrl import ArcInvestigation, OntologyAnnotation, Person  # type: ignore[import-untyped]

from middleware.payload.person_contacts import publication_authors


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
