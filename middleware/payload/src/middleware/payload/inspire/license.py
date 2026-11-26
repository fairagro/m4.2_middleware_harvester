"""INSPIRE / ISO 19139 ``gmd:otherConstraints`` → ``ARC.License``.

Shared ARCtrl path rules (``LICENSE`` file, not a URL ``@id``) live in
``middleware.payload.arc_license``; this module holds only the INSPIRE detection
heuristics used by ``inspire_general``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from urllib.parse import urlparse

from arctrl.py.license import License  # type: ignore[import-untyped]

_URL_RE = re.compile(r"https?://[^\s()<>\"';,]+")
# GeoNode licence text: "<name> (<identifier>): <description>", e.g.
# "CC-BY (CC-BY): https://creativecommons.org/licenses/by/4.0/ (https://…/legalcode)".
_GEONODE_LICENSE_RE = re.compile(r"^(?P<name>[^():]+?) \((?P<identifier>[^()]+)\):", re.DOTALL)
# GeoNode "no licence" entry: "Not Specified: The original author did not specify a license."
_NOT_SPECIFIED_RE = re.compile(r"^not specified\b", re.IGNORECASE)
# Hosts whose URLs identify a licence; used only for free-text INSPIRE constraints.
_LICENSE_HOSTS = (
    "creativecommons.org",
    "opendatacommons.org",
    "govdata.de",
    "spdx.org",
    "rightsstatements.org",
)
# INSPIRE code-list anchors (e.g. ConditionsApplyingToAccessAndUse) are not licences.
_INSPIRE_REGISTRY_HOSTS = ("inspire.ec.europa.eu",)


def _host_in(url: str, hosts: Iterable[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == h or host.endswith(f".{h}") for h in hosts)


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not any(c.isspace() for c in value)


def _license(text: str) -> License:
    return License("fulltext", text)


def _json_field_re(key: str) -> re.Pattern[str]:
    return re.compile(rf'"{key}\\?"\s*:\s*"([^"\\]*)"')


def _gdi_de_json_license(constraint: str) -> License | None:
    """Licence from a GDI-DE JSON constraint, e.g. ``{"id": "cc-by/4.0", "name": "…", "url": "https://…"}``.

    The GDI-DE metadata conventions put the licence as JSON into ``gmd:otherConstraints``.
    The licence is ``name (url)``, or the URL alone without a name; ``None`` without an http(s) URL.
    """
    if not constraint.startswith("{"):
        return None
    try:
        data = json.loads(constraint)
    except ValueError:
        # Malformed JSON seen in the wild (DWD: ``"name\": …``): read the two fields directly.
        data = {key: match.group(1) for key in ("name", "url") if (match := _json_field_re(key).search(constraint))}
    if not isinstance(data, dict):
        return None
    url = str(data.get("url") or "").strip()
    if not _is_http_url(url):
        return None
    name = str(data.get("name") or "").strip()
    return _license(f"{name} ({url})" if name else url)


def is_inspire_licence_url(url: str) -> bool:
    """Return whether ``url`` is an http(s) licence anchor (not an INSPIRE code-list URI)."""
    text = url.strip()
    return _is_http_url(text) and not _host_in(text, _INSPIRE_REGISTRY_HOSTS)


def is_inspire_licence_constraint(constraint: str) -> bool:
    """Return whether ``constraint`` is a licence-bearing ``gmd:otherConstraints`` value.

    Matches the shapes ``inspire_license`` can promote to ``ARC.License`` (GDI-DE JSON with
    http(s) ``url``, GeoNode ``Name (id): …`` text, free text with a known licence-host URL).
    GeoNode ``Not Specified`` and plain access notes are ``False``.
    """
    text = constraint.strip()
    if not text or _NOT_SPECIFIED_RE.match(text):
        return False
    if _gdi_de_json_license(text) is not None:
        return True
    if _GEONODE_LICENSE_RE.match(text):
        return True
    return any(_host_in(url, _LICENSE_HOSTS) for url in _URL_RE.findall(text))


def inspire_license(other_constraints: Iterable[str], other_constraints_url: Iterable[str]) -> License | None:
    """Return an ARC licence from ISO 19139 ``gmd:otherConstraints``, or ``None``.

    In order: the first GDI-DE JSON licence (``name (url)``); the first GeoNode-style licence
    text (``Name (id): description (url)``); the first text that contains a URL on a known
    licence host; else the first ``gmx:Anchor/@xlink:href`` that is not an INSPIRE code-list
    URI. Richer ``otherConstraints`` text wins over a bare anchor so DWD-shaped records keep
    ``name (url)`` when both JSON and a licence URL are present (#485 review). A GeoNode
    ``Not Specified`` entry, access notes and other free text yield no licence.
    """
    constraints = [c.strip() for c in other_constraints if c and c.strip()]
    if any(_NOT_SPECIFIED_RE.match(c) for c in constraints):
        return None
    for constraint in constraints:
        if license_ := _gdi_de_json_license(constraint):
            return license_
    for constraint in constraints:
        if _GEONODE_LICENSE_RE.match(constraint):
            return _license(constraint)
    for constraint in constraints:
        if any(_host_in(url, _LICENSE_HOSTS) for url in _URL_RE.findall(constraint)):
            return _license(constraint)
    for url in other_constraints_url:
        if is_inspire_licence_url(url):
            return _license(url.strip())
    return None
