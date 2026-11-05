"""Readers for the CSW ``GetCapabilities`` document.

OWSLib fetches and parses ``GetCapabilities`` when a :class:`CatalogueServiceWeb` is
constructed, so everything here is read off the already-cached response and costs no
extra request.

Every reader is total: a server that omits a field, or advertises it in an unexpected
shape, must degrade to "unknown" rather than raise. These run inside
``CSWClient._connect``, where an exception would fail the whole harvest to report
metadata we only use for logging and page-size clamping.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_MAX_RECORD_DEFAULT = "MaxRecordDefault"


def describe_service(csw: Any) -> str | None:  # noqa: ANN401
    """Return the endpoint's advertised service title, or None when it publishes none."""
    identification = getattr(csw, "identification", None)
    if identification is None:
        return None
    title = getattr(identification, "title", None)
    return title if isinstance(title, str) else None


def _first_int(value: object) -> int | None:
    """Coerce an OWSLib constraint value to a positive int, or None when it is not one.

    Constraint values arrive as a list of strings (``['10']``). Mirrors
    ``CSWClient._coerce_result_int``, duplicated rather than imported because
    ``csw_client`` imports this module.
    """
    if isinstance(value, (list, tuple)):
        return _first_int(value[0]) if value else None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        try:
            parsed = int(value)
        except ValueError:
            return None
        return parsed if parsed > 0 else None
    return None


def advertised_max_records(csw: Any) -> int | None:  # noqa: ANN401
    """Return the advertised ``MaxRecordDefault`` page size, or None when unavailable."""
    constraints = getattr(csw, "constraints", None)
    if not isinstance(constraints, dict):
        return None
    constraint = constraints.get(_MAX_RECORD_DEFAULT)
    if constraint is None:
        return None
    return _first_int(getattr(constraint, "values", None))


def clamp_page_size(page_size: int, advertised: int | None) -> int:
    """Return ``min(page_size, advertised)`` when ``advertised`` is positive and lower.

    Clamp down only — a higher advert never raises the request page size.
    """
    if advertised is not None and advertised < page_size:
        return advertised
    return page_size


def log_page_size_clamp(requested: int, advertised: int) -> None:
    """Log one INFO when the request page size is clamped to the advertised default."""
    logger.info(
        "CSW endpoint advertises MaxRecordDefault=%s, below the requested page size=%s; "
        "clamping request maxRecords to %s.",
        advertised,
        requested,
        advertised,
    )


@dataclass
class PageSizeClamp:
    """Clamp request page sizes to advertised ``MaxRecordDefault``; INFO at most once."""

    advertised: int | None = None
    _logged: bool = field(default=False, repr=False)

    @classmethod
    def from_csw(cls, csw: Any) -> PageSizeClamp:  # noqa: ANN401
        """Read ``MaxRecordDefault`` from capabilities without logging.

        INFO is emitted only from :meth:`apply` when a real request page size shrinks,
        so config ``chunk_size`` alone never produces a clamp log for an XML harvest
        whose effective page size is already at or below the advert.
        """
        return cls(advertised=advertised_max_records(csw))

    def apply(self, page_size: int) -> int:
        """Clamp ``page_size`` down and INFO once when the size actually shrinks."""
        clamped = clamp_page_size(page_size, self.advertised)
        if clamped < page_size and self.advertised is not None and not self._logged:
            log_page_size_clamp(page_size, self.advertised)
            self._logged = True
        return clamped


def note_server_caps_page_size(csw: Any) -> int | None:  # noqa: ANN401
    """Read ``MaxRecordDefault`` (test helper around :meth:`PageSizeClamp.from_csw`)."""
    return PageSizeClamp.from_csw(csw).advertised
