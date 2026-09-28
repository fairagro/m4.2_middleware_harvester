"""Unit tests for the shared identifier-sanitization helpers.

Extracted from `LinkedDataMapper` (issue #20 for `middleware.inspire`) so any mapper can
reuse them as plain functions — see `LinkedDataMapper.sanitize_identifier`/
`.to_identifier_slug`, now thin delegating wrappers around this module.
"""

from middleware.payload.identifier_sanitizer import sanitize_identifier, to_identifier_slug


def test_sanitize_identifier_strips_leading_scheme() -> None:
    assert sanitize_identifier("https://example.com/frl:12.3") == "example_com_frl_12_3"


def test_sanitize_identifier_allowlists_characters() -> None:
    assert sanitize_identifier("weird id!@#") == "weird id"


def test_sanitize_identifier_collapses_repeated_underscores() -> None:
    assert sanitize_identifier("a///b") == "a_b"


def test_to_identifier_slug_lowercases_and_replaces_non_alnum() -> None:
    assert to_identifier_slug("Test Dataset") == "test_dataset"


def test_to_identifier_slug_returns_none_for_empty_or_whitespace() -> None:
    assert to_identifier_slug("") is None
    assert to_identifier_slug("   ") is None


def test_to_identifier_slug_truncates_to_80_chars() -> None:
    result = to_identifier_slug("x" * 200)
    assert result is not None
    assert len(result) == 80
