"""Unit tests for exception formatting used in logs and harvest reports."""

import httpx
import pytest

from middleware.api_client.api_client import ApiClientError
from middleware.harvester.errors import format_exception_for_report


def test_format_exception_for_report_includes_read_timeout_cause() -> None:
    cause = httpx.ReadTimeout("")
    error = ApiClientError("Request failed: ", status_code=None)
    error.__cause__ = cause

    message = format_exception_for_report(error)

    assert "ApiClientError" in message
    assert "timeout" in message
    assert "Request failed: request timed out" in message
    assert "httpx.ReadTimeout" in message
    assert "request timed out" in message


def test_format_exception_for_report_keeps_http_status() -> None:
    error = ApiClientError("HTTP error 400: RDI unknown", status_code=400)

    message = format_exception_for_report(error)

    assert message == "ApiClientError [HTTP 400]: HTTP error 400: RDI unknown"


def test_format_exception_for_report_marks_plain_timeout() -> None:
    message = format_exception_for_report(httpx.ConnectTimeout(""))

    assert message == "httpx.ConnectTimeout [timeout]: request timed out"


@pytest.mark.parametrize(
    ("exc", "needle"),
    [
        (RuntimeError("boom"), "RuntimeError: boom"),
        (ValueError(""), "ValueError: (no message)"),
    ],
)
def test_format_exception_for_report_generic_exceptions(exc: Exception, needle: str) -> None:
    assert format_exception_for_report(exc) == needle
