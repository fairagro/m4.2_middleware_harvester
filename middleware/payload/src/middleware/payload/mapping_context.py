"""Per-call discovery context for ``DataMapper.map``."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import ConfigDict, HttpUrl, TypeAdapter
from pydantic.dataclasses import dataclass

_HTTP_URL = TypeAdapter(HttpUrl)


def as_source_url(value: str | None) -> HttpUrl | None:
    """Coerce an optional http(s) URL string to ``HttpUrl`` for ``MappingContext``."""
    if value is None or not value.strip():
        return None
    return _HTTP_URL.validate_python(value.strip())


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

    source_url: HttpUrl | None = None
    harvest_source_id: str | None = None
    html_title: Callable[[], str | None] | None = None
