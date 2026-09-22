"""Readers for the CSW ``GetCapabilities`` document.

OWSLib fetches and parses ``GetCapabilities`` when a :class:`CatalogueServiceWeb` is
constructed, so everything here is read off the already-cached response and costs no
extra request.

Every reader is total: a server that omits a field, or advertises it in an unexpected
shape, must degrade to "unknown" rather than raise. These run inside
``CSWClient._connect``, where an exception would fail the whole harvest to report
metadata we only use for logging.
"""

import logging
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


def warn_if_server_caps_page_size(csw: Any, chunk_size: int) -> None:  # noqa: ANN401
    """Warn when the endpoint advertises a page size below the configured chunk_size.

    Some servers enforce ``MaxRecordDefault`` as a ceiling, which makes a larger
    ``chunk_size`` inert: the harvest still completes, because pagination follows the
    response's ``nextrecord`` / ``returned``, but it issues the same number of requests
    as if ``chunk_size`` matched the cap. Without this line that is invisible.

    The value is a *default* per CSW 2.0.2, not a documented ceiling, so we report the
    discrepancy and still request ``chunk_size``.
    """
    advertised = advertised_max_records(csw)
    if advertised is None or advertised >= chunk_size:
        return
    logger.warning(
        "CSW endpoint advertises MaxRecordDefault=%s, below the configured chunk_size=%s; "
        "the server may cap pages at %s, so a larger chunk_size will not reduce the request count.",
        advertised,
        chunk_size,
        advertised,
    )
