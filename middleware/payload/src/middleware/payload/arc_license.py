"""Build the ARC licence (``ARC.License``) from source licence metadata.

Without ``ARC.License`` the ARCtrl RO-Crate writer emits its default ``#LICENSE`` node
("ALL RIGHTS RESERVED BY THE AUTHORS"). Mappers set the licence when the source states one
and otherwise leave that default in place: no licence granted means all rights reserved.

ARCtrl treats ``License.Path`` as the licence *file* inside the ARC and reads it back from
the RO-Crate licence ``@id``. A URL there makes ``ARC.Write`` create ``https:/…`` directories
(the API writes ARCs from these RO-Crates), so the licence always keeps the default ``LICENSE``
path and carries the licence URL and text as its content.

INSPIRE ``gmd:otherConstraints`` detection lives in ``middleware.payload.inspire.license``.
"""

from __future__ import annotations

from urllib.parse import urlparse

from arctrl.py.license import License  # type: ignore[import-untyped]

from middleware.payload.placeholders import PlaceholderConfig


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
