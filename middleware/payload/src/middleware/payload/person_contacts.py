"""Validation helpers for ARC Person contacts produced by mappers."""

from __future__ import annotations

import re

from arctrl import ArcInvestigation, OntologyAnnotation, Person  # type: ignore[import-untyped]

# Bare ORCID iD or orcid.org URL; the last character is a checksum digit or "X".
_ORCID_RE = re.compile(r"^(?:https?://(?:www\.)?orcid\.org/)?(\d{4}-\d{4}-\d{4}-\d{3}[\dX])/?$", re.IGNORECASE)


def orcid_id(value: str | None) -> str | None:
    """Return the bare ORCID iD (``0000-0002-1825-0097``) of an iD or orcid.org URL, else ``None``."""
    match = _ORCID_RE.match((value or "").strip())
    return match.group(1).upper() if match else None


def add_contact(investigation: ArcInvestigation, person: Person, role: str) -> None:
    """Append ``person`` with ``role``, or add ``role`` to the contact that already has its ORCID.

    ARCtrl uses the ORCID as the RO-Crate Person ``@id``, so two contacts with the same ORCID
    would collapse into one node carrying both roles; keep one contact per ORCID instead.
    """
    if person.ORCID:
        for contact in investigation.Contacts:
            if contact.ORCID == person.ORCID:
                if not any((r.Name or "").casefold() == role.casefold() for r in contact.Roles):
                    contact.Roles.append(OntologyAnnotation(name=role))
                return
    person.Roles.append(OntologyAnnotation(name=role))
    investigation.Contacts.append(person)


def require_nonempty_person_given_names(investigation: ArcInvestigation) -> None:
    """Raise ``ValueError`` if any contact lacks a non-empty trimmed given name.

    Placeholder values MUST NOT be substituted; callers must omit or remap
    organizations before invoking this check.
    """
    for person in investigation.Contacts:
        given = person.FirstName
        if given is None or not str(given).strip():
            last = person.LastName or ""
            raise ValueError(f"Person contact must have a non-empty given name (last_name={last!r})")


def publication_authors(investigation: ArcInvestigation) -> str | None:
    """Build a ``Publication.authors`` string from author-role contacts, in contact order.

    Each author is ``F. Last`` (``Last`` or ``First`` alone when the other is missing), joined
    by ``"; "``. The RO-Crate writer splits ``Publication.authors`` on ``","``, so the
    ``Last, F.`` form MUST NOT be used. Role names match case-insensitively (``author`` /
    NCIT ``Author``).
    """
    author_strs: list[str] = []
    for person in investigation.Contacts:
        if not any((role.Name or "").casefold() == "author" for role in person.Roles):
            continue
        first = (person.FirstName or "").strip()
        last = (person.LastName or "").strip()
        if first and last:
            author_strs.append(f"{first[0]}. {last}")
        elif last or first:
            author_strs.append(last or first)
    return "; ".join(author_strs) if author_strs else None
