"""Core exceptions for the Middleware Harvester ecosystem.

This module provides the overarching exception hierarchy used by the orchestrator
and all plugins to standardize error handling and logging.
"""

from __future__ import annotations

from dataclasses import dataclass

_TIMEOUT_TYPE_NAMES = frozenset(
    {
        "TimeoutException",
        "ReadTimeout",
        "WriteTimeout",
        "ConnectTimeout",
        "PoolTimeout",
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


def _format_exception_segment(exc: BaseException) -> str:
    """Format a single exception without walking its cause chain."""
    label = _exception_type_label(exc)
    message = str(exc).strip()
    status_code = getattr(exc, "status_code", None)

    qualifiers: list[str] = []
    if _is_timeout_exception(exc):
        qualifiers.append("timeout")
    if isinstance(status_code, int):
        qualifiers.append(f"HTTP {status_code}")
    elif status_code is None and type(exc).__name__ == "ApiClientError" and exc.__cause__ is not None:
        # Connection/timeout failures from the API client have no HTTP status.
        if _is_timeout_exception(exc.__cause__):
            qualifiers.append("timeout")
        else:
            qualifiers.append("connection/request error")

    suffix = f" [{', '.join(qualifiers)}]" if qualifiers else ""

    if _is_timeout_exception(exc) and not message:
        return f"{label}{suffix}: request timed out"

    # ApiClient often builds "Request failed: " with an empty httpx message.
    if message in {"Request failed:", "Request failed"}:
        if _is_timeout_exception(exc) or (exc.__cause__ is not None and _is_timeout_exception(exc.__cause__)):
            return f"{label}{suffix}: Request failed: request timed out"
        return f"{label}{suffix}: Request failed: (no details from client)"

    if message:
        return f"{label}{suffix}: {message}"

    return f"{label}{suffix}: (no message)"


def format_exception_for_report(exc: BaseException) -> str:
    """Build a log/report message that keeps timeout and cause details visible.

    ``ApiClientError`` often wraps ``httpx.ReadTimeout`` (and similar) with an
    empty string representation, which previously produced useless messages like
    ``Request failed: ``. This helper always includes the exception type and walks
    ``__cause__`` so operators can see e.g. ``httpx.ReadTimeout [timeout]``.
    """
    parts: list[str] = []
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        parts.append(_format_exception_segment(current))
        current = current.__cause__
    return " — caused by ".join(parts)
