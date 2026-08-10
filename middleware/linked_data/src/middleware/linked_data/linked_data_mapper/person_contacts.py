"""Validation helpers for ARC Person contacts produced by linked-data mappers."""

from __future__ import annotations

from arctrl import ArcInvestigation  # type: ignore[import-untyped]


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
