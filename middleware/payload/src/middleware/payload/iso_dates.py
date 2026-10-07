"""Normalise source date strings to ISO 8601 for ARC date fields.

ISO 8601 dates and date-times (``2011``, ``2011-01``, ``2011-01-01``, ``2011-01-01T10:00:00.123Z``)
pass through unchanged. Java ``Date.toString()`` values (``Sat Jan 01 00:00:00 CET 2011``, used by
e!DAL) become an ISO date-time with the offset of their time-zone abbreviation, so the local
calendar day is kept. Anything else is not a date: ``iso_date`` returns ``None``.
"""

from __future__ import annotations

import re
from datetime import datetime

# Same shape as the INSPIRE ``IsoDate`` model type (gco:Date / gco:DateTime).
_ISO_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,9})?)?(Z|[+-]\d{2}:?\d{2})?)?)?)?$")
# Java Date.toString(): "EEE MMM dd HH:mm:ss zzz yyyy".
_JAVA_RE = re.compile(
    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (?P<month>[A-Z][a-z]{2}) (?P<day>\d{1,2}) "
    r"(?P<time>\d{2}:\d{2}:\d{2}) (?P<zone>[A-Z]{2,5}) (?P<year>\d{4})$"
)
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
# Unambiguous abbreviations only; others (e.g. "IST", "CST") make the value unparseable.
_ZONE_OFFSETS = {
    "UTC": "+00:00",
    "GMT": "+00:00",
    "WET": "+00:00",
    "WEST": "+01:00",
    "CET": "+01:00",
    "CEST": "+02:00",
    "EET": "+02:00",
    "EEST": "+03:00",
}


def iso_date(value: str | None) -> str | None:
    """Return ``value`` as an ISO 8601 date or date-time, or ``None`` if it is not one."""
    text = (value or "").strip()
    if not text:
        return None
    if _ISO_RE.match(text):
        return text
    match = _JAVA_RE.match(text)
    if not match or match["month"] not in _MONTHS or match["zone"] not in _ZONE_OFFSETS:
        return None
    try:  # month index, not strptime("%b"), which depends on the process locale
        day = datetime(int(match["year"]), _MONTHS.index(match["month"]) + 1, int(match["day"]))  # noqa: DTZ001
    except ValueError:
        return None
    return f"{day:%Y-%m-%d}T{match['time']}{_ZONE_OFFSETS[match['zone']]}"
