"""Normalise source DOI strings to the bare ``10.<registrant>/<suffix>`` form.

Sources write DOIs as ``doi:`` CURIEs, ``doi.org`` / ``dx.doi.org`` URLs, or both stacked
(GeoNode CSW: ``doi:https://doi.org/10.4228/…``, ``https://dx.doi.org/https://doi.org/…``).
All prefixes are stripped, so a ``doi:`` CURIE never reaches the RO-Crate, where JSON-LD
expansion would turn it into ``https://dx.doi.org/<rest>``.
"""

from __future__ import annotations

import re

_DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:www\.|dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
_DOI_RE = re.compile(r"^10\.\d+(?:\.\d+)*/\S+$")


def normalize_doi(raw: str | None) -> str | None:
    """Return the bare DOI in ``raw``, or ``None`` if ``raw`` is not a DOI."""
    text = (raw or "").strip()
    previous = None
    while text != previous:
        previous = text
        text = _DOI_PREFIX_RE.sub("", text).strip()
    return text if _DOI_RE.match(text) else None
