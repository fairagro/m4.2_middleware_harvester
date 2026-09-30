"""Per-call discovery context for ``DataMapper.map``."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import ConfigDict, HttpUrl, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass

_HTTP_URL = TypeAdapter(HttpUrl)


def as_source_url(value: str | None) -> str | None:
    """Validate an optional http(s) URL string without rewriting it.

    Pydantic ``HttpUrl`` re-serialization is not identity-preserving (percent-encoding,
    trailing slash, host case). Callers sanitize / reuse the original discovery URL for
    stable ARC identifiers, so we validate then return the stripped input unchanged.
    """
    if value is None or not value.strip():
        return None
    stripped = value.strip()
    try:
        _HTTP_URL.validate_python(stripped)
    except ValidationError as exc:
        raise ValueError(f"source_url must be an http(s) URL, got {stripped!r}") from exc
    return stripped


@dataclass(frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class MappingContext:
    """Per-call discovery extras for ``DataMapper.map`` (not mapper instance state).

    Carries what the harvest plugin knows about *this* record but that is not
    (or not yet) in the intermediate payload. Mappers must not store this on
    ``self`` — plugins map concurrently via ``asyncio.to_thread``.

    ``source_url`` is an ``http://`` / ``https://`` landing or page URL, or
    ``None``. Opaque catalog / OAI identifiers belong in ``harvest_source_id``.
    Pass strings through :func:`as_source_url` at construction sites.
    """

    source_url: str | None = None
    harvest_source_id: str | None = None
    html_title: Callable[[], str | None] | None = None
