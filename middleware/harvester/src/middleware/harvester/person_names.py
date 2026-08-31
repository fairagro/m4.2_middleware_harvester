"""Shared display-name splitting for ARC Person contacts.

When only a display string is available (INSPIRE CI_ResponsibleParty name,
Schema.org ``schema:name`` / literal creator), this module uses ``nameparser``
so titles, suffixes, particles (e.g. ``de la``), and ``Family, Given`` forms
are handled consistently.

Regal agent ``skos:prefLabel`` values follow the PUBLISSO ``Family, Given``
convention and MUST keep the Regal comma-split — they MUST NOT use this helper.
"""

from __future__ import annotations

from dataclasses import dataclass

from nameparser import parse


@dataclass(frozen=True)
class PersonNameParts:
    """Given/family parts suitable for ARC ``Person`` contacts.

    ``given`` is ``None`` when the display string does not yield a usable given
    name (single-token org-like labels, empty input, or family-only parses).
    """

    given: str | None
    family: str


def split_display_name(name: str) -> PersonNameParts:
    """Split a human display name into given and family parts.

    Middle names are folded into ``given`` (ARC has no middle-name field).
    Titles and suffixes are dropped. A single token with no family name is
    treated as an unlabeled agent (``given=None``, ``family=<token>``) so
    callers can fail closed or remap organizations — matching the
    person-contact-given-name policy for linked-data.
    """
    stripped = name.strip()
    if not stripped:
        return PersonNameParts(given=None, family="")

    parsed = parse(stripped)
    given_bits = [part.strip() for part in (parsed.given, parsed.middle) if part and part.strip()]
    given = " ".join(given_bits) or None
    family = (parsed.family or "").strip()

    # nameparser assigns a lone token to ``given`` with empty ``family``.
    # For Person contacts that is not a reliable split; keep fail-closed semantics.
    if given and not family:
        return PersonNameParts(given=None, family=given)

    if not given:
        return PersonNameParts(given=None, family=family)

    return PersonNameParts(given=given, family=family)
