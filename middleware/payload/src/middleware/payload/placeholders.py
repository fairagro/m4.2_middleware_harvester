"""Recognise placeholder text that RDIs write instead of leaving a field empty.

BonaRes and Thünen (GeoNode CSW) fill optional ISO 19139 elements with ``None`` or
``No information provided``; e!DAL renders an unexpanded ``$licenseURL`` template. These
are not metadata and are treated as absent. Matching is exact on the whole value
(case-insensitive, surrounding whitespace ignored), so a sentence that merely contains
"none" is kept. Unrendered ``$var`` / ``${var}`` / ``{{var}}`` templates always match.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

DEFAULT_PLACEHOLDER_VALUES: frozenset[str] = frozenset({
    "none",
    "null",
    "n/a",
    "no abstract provided",
    "keine zusammenfassung vorhanden",
    "no information provided",
})

_TEMPLATE_RE = re.compile(r"^(?:\$\{?[A-Za-z_]\w*\}?|\{\{\s*[A-Za-z_][\w.]*\s*\}\})$")


def normalize_placeholder_values(values: Iterable[str]) -> frozenset[str]:
    """Return ``values`` in the folded form :func:`is_placeholder` compares against."""
    return frozenset(v.strip().casefold() for v in values if v.strip())


def is_placeholder(value: str, values: frozenset[str] = DEFAULT_PLACEHOLDER_VALUES) -> bool:
    """Whether ``value`` is a placeholder from ``values`` (already folded) or an unrendered template."""
    text = value.strip()
    return text.casefold() in values or bool(_TEMPLATE_RE.match(text))
