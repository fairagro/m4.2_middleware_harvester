"""Core exceptions for the Middleware Harvester ecosystem.

This module provides the overarching exception hierarchy used by the orchestrator
and all plugins to standardize error handling and logging.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HARVEST_ID_IN_URL = re.compile(r"/v3/harvests/([^/?#]+)")

_TIMEOUT_TYPE_NAMES = frozenset(
    {
        "TimeoutException",
        "TimeoutError",
        "ReadTimeout",
        "WriteTimeout",
        "ConnectTimeout",
        "PoolTimeout",
    }
)

_CONNECTION_TYPE_NAMES = frozenset(
    {
        "ConnectError",
        "ConnectTimeout",
        "NetworkError",
        "ProxyError",
        "UnsupportedProtocol",
        "ProtocolError",
        "RemoteProtocolError",
        "LocalProtocolError",
        "ReadError",
        "WriteError",
        "CloseError",
    }
)


class HarvesterError(Exception):
    """Base exception for all Harvester and plugin-related errors."""


@dataclass(frozen=True)
class SkippedRecord:
    """Signal that a record was intentionally skipped during harvesting."""

    reason: str
    url: str | None = None

    def __str__(self) -> str:
        """Return the human-readable skip reason."""
        return self.reason


class RecordProcessingError(HarvesterError):
    """Raised when a specific record fails to be processed, carrying its identifier."""

    def __init__(self, message: str, record_id: str, original_error: Exception | None = None, url: str | None = None):
        """
        Initialize the RecordProcessingError.

        Args:
            message (str): The error message describing the issue.
            record_id (str): The identifier of the record that caused the error.
            original_error (Exception | None): The original exception that caused this error, if any.
            url (str | None): The source URL of the dataset, if available.
        """
        super().__init__(message)
        self.record_id = record_id
        self.original_error = original_error
        self.url = url

    def __str__(self) -> str:
        """Return a string representation including the record ID."""
        base = super().__str__()
        return f"{base} (record_id={self.record_id})"


def _exception_type_label(exc: BaseException) -> str:
    """Return a short type label, preferring httpx.* for httpx exceptions."""
    module = type(exc).__module__
    name = type(exc).__name__
    if module == "httpx" or module.startswith("httpx."):
        return f"httpx.{name}"
    return name


def _is_timeout_exception(exc: BaseException) -> bool:
    """Return True when *exc* is an HTTP client timeout (by type name)."""
    return type(exc).__name__ in _TIMEOUT_TYPE_NAMES


def _is_connection_exception(exc: BaseException) -> bool:
    """Return True for transport-level connection/network failures.

    Matches httpx transport error type names and ``ConnectionError`` (including
    subclasses such as ``ConnectionResetError``). Broader ``OSError`` subtypes
    like ``FileNotFoundError`` are intentionally excluded.
    """
    name = type(exc).__name__
    return name in _CONNECTION_TYPE_NAMES or isinstance(exc, ConnectionError)


def _httpx_request_target(exc: BaseException) -> str | None:
    """Return ``METHOD URL`` from an httpx RequestError when available."""
    try:
        request = getattr(exc, "request", None)
    except RuntimeError:
        # httpx raises when RequestError.request was never attached.
        return None
    if request is None:
        return None
    method = getattr(request, "method", None)
    url = getattr(request, "url", None)
    if method and url:
        return f"{method} {url}"
    if url:
        return str(url)
    return None


def failure_url_for_exception(exc: BaseException) -> str | None:
    """Return the HTTP request URL from an exception cause chain, if any."""
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        try:
            request = getattr(current, "request", None)
        except RuntimeError:
            request = None
        url = getattr(request, "url", None) if request is not None else None
        if url is not None:
            return str(url)
        current = current.__cause__
    return None


def harvest_id_from_exception(exc: BaseException) -> str | None:
    """Recover a harvest id from *exc* when ``harvest_arcs`` fails after create.

    Prefers an explicit ``harvest_id`` attribute on the exception chain (if the
    API client attaches one), otherwise parses ``/v3/harvests/{id}`` from a
    request URL carried by httpx errors.
    """
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        attached = getattr(current, "harvest_id", None)
        if isinstance(attached, str) and attached.strip():
            return attached.strip()
        current = current.__cause__

    url = failure_url_for_exception(exc)
    if not url:
        return None
    match = _HARVEST_ID_IN_URL.search(url)
    return match.group(1) if match else None


def _os_error_detail(exc: BaseException) -> str | None:
    """Return errno/strerror details for OSError-like exceptions."""
    if not isinstance(exc, OSError):
        return None
    parts: list[str] = []
    if getattr(exc, "errno", None) is not None:
        parts.append(f"errno {exc.errno}")
    strerror = getattr(exc, "strerror", None) or (str(exc.args[1]) if len(exc.args) > 1 else None)
    if strerror:
        parts.append(str(strerror))
    elif str(exc).strip():
        parts.append(str(exc).strip())
    return ", ".join(parts) if parts else None


def _category_for_exception(exc: BaseException) -> str | None:
    """Return a short operator-facing category for the exception."""
    status_code = getattr(exc, "status_code", None)
    category: str | None = None
    if isinstance(status_code, int):
        category = f"HTTP {status_code}"
    elif _is_timeout_exception(exc):
        category = "timeout"
    elif type(exc).__name__ == "ApiClientError" and exc.__cause__ is not None:
        if _is_timeout_exception(exc.__cause__):
            category = "timeout"
        elif _is_connection_exception(exc.__cause__):
            category = "API connection failed (request may not have reached the server)"
        else:
            category = "API request error"
    elif type(exc).__name__ == "ConnectError":
        category = "connection failed before HTTP response"
    elif _is_connection_exception(exc):
        category = "connection/network error"
    return category


def _detail_for_exception(exc: BaseException) -> str:
    """Build the human-readable detail part for one exception segment."""
    message = str(exc).strip()
    request_target = _httpx_request_target(exc)
    os_detail = _os_error_detail(exc)

    bits: list[str] = []
    if request_target:
        bits.append(f"while calling {request_target}")

    if _is_timeout_exception(exc) and not message:
        bits.append("request timed out")
    elif message in {"Request failed:", "Request failed"}:
        cause = exc.__cause__
        if cause is not None and _is_timeout_exception(cause):
            bits.append("Request failed: request timed out")
        elif cause is not None and _is_connection_exception(cause):
            bits.append(
                "Request failed: could not establish or keep TCP/TLS connection to the Middleware API "
                "(often leaves no API-side log entry)"
            )
        else:
            bits.append("Request failed: (no details from client)")
    elif os_detail:
        # Prefer structured errno/strerror over str(OSError) ("[Errno N] ...") to avoid
        # near-duplicate detail when both forms would otherwise be appended.
        bits.append(os_detail)
    elif message:
        bits.append(message)
    elif _is_timeout_exception(exc):
        bits.append("request timed out")
    else:
        bits.append("(no message)")

    return "; ".join(bits)


def _format_exception_segment(exc: BaseException) -> str:
    """Format a single exception without walking its cause chain."""
    label = _exception_type_label(exc)
    category = _category_for_exception(exc)
    suffix = f" [{category}]" if category else ""
    return f"{label}{suffix}: {_detail_for_exception(exc)}"


def format_exception_for_report(exc: BaseException) -> str:
    """Build a log/report message that keeps timeout and cause details visible.

    ``ApiClientError`` often wraps ``httpx.ConnectError`` / ``ReadTimeout`` with an
    empty string representation. This helper always includes exception types, the
    attempted HTTP target when present on the httpx error, OS-level errno details,
    and walks ``__cause__``.
    """
    parts: list[str] = []
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        parts.append(_format_exception_segment(current))
        current = current.__cause__
    return " — caused by ".join(parts)
