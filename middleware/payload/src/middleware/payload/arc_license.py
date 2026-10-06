"""Build the ARC licence (``ARC.License``) from source licence metadata.

Without ``ARC.License`` the ARCtrl RO-Crate writer emits its default ``#LICENSE`` node
("ALL RIGHTS RESERVED BY THE AUTHORS"). Mappers set the licence when the source states one
and otherwise leave that default in place: no licence granted means all rights reserved.

ARCtrl treats ``License.Path`` as the licence *file* inside the ARC and reads it back from
the RO-Crate licence ``@id``. A URL there makes ``ARC.Write`` create ``https:/…`` directories
(the API writes ARCs from these RO-Crates), so the licence always keeps the default ``LICENSE``
path and carries the licence URL and text as its content.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import urlparse

from arctrl.py.license import License  # type: ignore[import-untyped]

from middleware.payload.placeholders import PlaceholderConfig

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


def license_from_value(
    value: str | None,
    *,
    placeholders: PlaceholderConfig,
    name: str | None = None,
) -> License | None:
    """Return an ARC licence for a source value that is declared to be a licence.

    For schema.org ``license`` and Regal ``license``: the value (URL or text) becomes the
    licence content, as ``name (url)`` when a CreativeWork ``name`` accompanies a URL. Empty
    values and the RDI's ``placeholders`` (e.g. an unexpanded ``$licenseURL``) return ``None``.
    """
    text = (value or "").strip()
    if not text or placeholders.matches(text):
        return None
    label = (name or "").strip()
    if label and label != text and _is_http_url(text):
        return _license(f"{label} ({text})")
    return _license(text)


def inspire_license(other_constraints: Iterable[str], other_constraints_url: Iterable[str]) -> License | None:
    """Return an ARC licence from ISO 19139 ``gmd:otherConstraints``, or ``None``.

    In order: the first ``gmx:Anchor/@xlink:href`` that is not an INSPIRE code-list URI; the
    first GeoNode-style licence text (``Name (id): description (url)``); the first text that
    contains a URL on a known licence host. A GeoNode ``Not Specified`` entry, access notes
    and other free text yield no licence.
    """
    for url in other_constraints_url:
        url = url.strip()
        if _is_http_url(url) and not _host_in(url, _INSPIRE_REGISTRY_HOSTS):
            return _license(url)

    constraints = [c.strip() for c in other_constraints if c and c.strip()]
    if any(_NOT_SPECIFIED_RE.match(c) for c in constraints):
        return None
    for constraint in constraints:
        if _GEONODE_LICENSE_RE.match(constraint):
            return _license(constraint)
    for constraint in constraints:
        if any(_host_in(url, _LICENSE_HOSTS) for url in _URL_RE.findall(constraint)):
            return _license(constraint)
    return None
