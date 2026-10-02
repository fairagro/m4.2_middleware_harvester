"""Validation helpers for ARC Person contacts produced by mappers."""

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
