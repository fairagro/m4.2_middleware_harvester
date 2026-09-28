"""Defensive bounds for harvested INSPIRE CSW/ISO-19139 values.

Every value extracted by `IsoParser` comes from a remote CSW server and is untrusted
(`openspec/principles.md`: "Security by default" — external input is validated before
use). Today those values are type-guarded but otherwise unbounded: a hostile or broken
server can return arbitrarily long strings, arbitrarily long lists, or URLs with any
scheme (`javascript:`, `file:`, `data:`, ...).

These helpers apply defensive-only bounds — length caps, list-count caps, and an
http(s)-only URL allowlist. They are NOT semantic/data-quality validation: a value that
passes here may still be nonsensical (a malformed date, an out-of-range bounding box, an
unreachable URL) — that is explicitly out of scope, tracked separately (see
`openspec/changes/2026-09-28-bound-inspire-harvested-values/proposal.md` Non-Goals and
issue #132).

Every function here drops or truncates rather than raises, matching the existing
drop-bad-element convention already used by sibling extractors in `iso_parser.py` (e.g.
`_extract_identification_list`'s `if isinstance(i, str)` silently omits non-string
elements today). Bounding one field must never fail an otherwise-parseable record.

See `openspec/specs/inspire-value-bounds/`.
"""

from urllib.parse import urlsplit

# Short codes/labels (edition, status).
MAX_STR_SHORT = 200

# Title-length free text, list-element strings, URL fields' own length, contact
# name/organization, and similar single-line-ish fields.
MAX_STR_MEDIUM = 1_000

# Paragraph-length free text: abstract, lineage, supplemental_information.
MAX_STR_LONG = 10_000

# Shared cap for every unbounded list field on InspireRecord.
MAX_LIST_ITEMS = 500

_ALLOWED_URL_SCHEMES = {"http", "https"}


def truncate(value: str, max_len: int = MAX_STR_MEDIUM) -> str:
    """Truncate a required (non-``None``) string to at most ``max_len`` characters."""
    return value[:max_len]


def bounded_str(value: str | None, max_len: int = MAX_STR_MEDIUM) -> str | None:
    """Truncate an optional string to at most ``max_len`` characters, passing ``None`` through."""
    if value is None:
        return None
    return truncate(value, max_len)


def bounded_list[T](items: list[T], max_items: int = MAX_LIST_ITEMS) -> list[T]:
    """Cap a list to its first ``max_items`` elements."""
    return items[:max_items]


def valid_http_url(value: str | None, max_len: int = MAX_STR_MEDIUM) -> str | None:
    """Return ``value`` if it is a well-formed, reasonably-sized http(s) URL, else ``None``.

    Rejects (returns ``None`` for, never raises): empty/whitespace values, values over
    ``max_len``, any non-http(s) scheme (``javascript:``, ``file:``, ``data:``, ``ftp:``,
    ...), and protocol-relative URLs (``//host/path``, empty scheme) — a scheme this
    harvester never dereferences, so requiring an explicit ``http``/``https`` is a
    security boundary, not a data-quality judgment.
    """
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > max_len:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES or not parsed.netloc:
        return None
    return value
