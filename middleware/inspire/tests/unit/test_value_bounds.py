"""Unit tests for defensive value-bounding helpers.

These guard `openspec/specs/inspire-value-bounds/`. Pure functions, no OWSLib/CSW
fixtures needed.
"""

import pytest

from middleware.inspire.value_bounds import (
    MAX_STR_MEDIUM,
    bounded_list,
    bounded_str,
    truncate,
    valid_http_url,
)


def test_truncate_leaves_short_value_unchanged() -> None:
    assert truncate("short", 10) == "short"


def test_truncate_cuts_long_value_to_exact_length() -> None:
    assert truncate("x" * 20, 10) == "x" * 10


def test_bounded_str_passes_none_through() -> None:
    assert bounded_str(None, 10) is None


def test_bounded_str_truncates_like_truncate() -> None:
    assert bounded_str("x" * 20, 10) == "x" * 10


def test_bounded_list_leaves_short_list_unchanged() -> None:
    items = [1, 2, 3]
    assert bounded_list(items, 10) == items


def test_bounded_list_caps_long_list_preserving_order() -> None:
    items = list(range(1000))
    result = bounded_list(items, 5)
    assert result == [0, 1, 2, 3, 4]


@pytest.mark.parametrize(
    "value",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "data:text/html,<script>alert(1)</script>",
        "ftp://example.com/file",
        "//evil.example/x",  # protocol-relative
        "",
        "   ",
        None,
    ],
)
def test_valid_http_url_rejects_dangerous_or_empty_values(value: str | None) -> None:
    assert valid_http_url(value) is None


def test_valid_http_url_rejects_oversized_value() -> None:
    oversized = "http://example.com/" + ("x" * MAX_STR_MEDIUM)
    assert valid_http_url(oversized) is None


@pytest.mark.parametrize(
    "value",
    [
        "http://example.com/thumb.png",
        "https://example.com/csw",
        "https://example.com:8443/path?query=1",
    ],
)
def test_valid_http_url_passes_through_well_formed_urls(value: str) -> None:
    assert valid_http_url(value) == value
