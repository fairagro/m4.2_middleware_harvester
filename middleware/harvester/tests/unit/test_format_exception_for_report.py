"""Unit tests for exception formatting used in logs and harvest reports."""

import httpx
import pytest

from middleware.api_client.api_client import ApiClientError
from middleware.harvester.errors import (
    failure_url_for_exception,
    format_exception_for_report,
    harvest_id_from_exception,
)


def test_format_exception_for_report_includes_read_timeout_cause() -> None:
    cause = httpx.ReadTimeout("")
    error = ApiClientError("Request failed: ", status_code=None)
    error.__cause__ = cause

    message = format_exception_for_report(error)

    assert "ApiClientError" in message
    assert "timeout" in message
    assert "request timed out" in message
    assert "httpx.ReadTimeout" in message


def test_format_exception_for_report_keeps_http_status() -> None:
    error = ApiClientError("HTTP error 400: RDI unknown", status_code=400)

    message = format_exception_for_report(error)

    assert message == "ApiClientError [HTTP 400]: HTTP error 400: RDI unknown"


def test_format_exception_for_report_marks_plain_timeout() -> None:
    message = format_exception_for_report(httpx.ConnectTimeout(""))

    assert "httpx.ConnectTimeout [timeout]" in message
    assert "request timed out" in message


def test_format_exception_for_report_includes_connect_error_request_and_errno() -> None:
    request = httpx.Request("POST", "https://middleware-test.example/v3/harvests/h1/arcs")
    os_err = ConnectionResetError(104, "Connection reset by peer")
    cause = httpx.ConnectError("", request=request)
    cause.__cause__ = os_err
    error = ApiClientError("Request failed: ", status_code=None)
    error.__cause__ = cause

    message = format_exception_for_report(error)

    assert "API connection failed" in message
    assert "POST https://middleware-test.example/v3/harvests/h1/arcs" in message
    assert "httpx.ConnectError" in message
    assert "connection failed before HTTP response" in message
    assert "errno 104" in message
    assert "Connection reset by peer" in message
    assert failure_url_for_exception(error) == "https://middleware-test.example/v3/harvests/h1/arcs"
    assert harvest_id_from_exception(error) == "h1"


def test_harvest_id_from_exception_prefers_explicit_attribute() -> None:
    error = ApiClientError("Request failed: ", status_code=None)
    error.harvest_id = "harvest-explicit"  # type: ignore[attr-defined]

    assert harvest_id_from_exception(error) == "harvest-explicit"


def test_harvest_id_from_exception_returns_none_without_url_or_attribute() -> None:
    assert harvest_id_from_exception(RuntimeError("boom")) is None


def test_format_exception_for_report_does_not_duplicate_oserror_detail() -> None:
    message = format_exception_for_report(ConnectionResetError(104, "Connection reset by peer"))

    assert message.count("Connection reset by peer") == 1
    assert "errno 104" in message
    assert "[Errno 104]" not in message


def test_format_exception_for_report_does_not_treat_file_not_found_as_connection() -> None:
    message = format_exception_for_report(FileNotFoundError(2, "No such file"))

    assert "connection/network error" not in message
    assert "FileNotFoundError" in message
    assert "errno 2" in message


@pytest.mark.parametrize(
    ("exc", "needle"),
    [
        (RuntimeError("boom"), "RuntimeError: boom"),
        (ValueError(""), "ValueError: (no message)"),
    ],
)
def test_format_exception_for_report_generic_exceptions(exc: Exception, needle: str) -> None:
    assert format_exception_for_report(exc) == needle
