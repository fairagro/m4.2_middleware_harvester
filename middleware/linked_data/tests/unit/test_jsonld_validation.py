"""JSON-LD @context validation unit tests."""

import pytest

from middleware.linked_data.jsonld_validation import (
    SCHEMAORG_CONTEXT_ALLOWLIST,
    JsonLdContextError,
    validate_jsonld_context,
)


def test_allowlist_matches_expected_contexts() -> None:
    """Exact membership — avoid ``url in container`` which CodeQL flags as substring sanitization."""
    expected = frozenset(
        {
            "https://schema.org/",
            "http://schema.org/",
            "https://schema.org",
            "http://schema.org",
            "https://bioschemas.org/",
            "http://bioschemas.org/",
            "https://bioschemas.org",
            "http://bioschemas.org",
        }
    )
    assert expected == SCHEMAORG_CONTEXT_ALLOWLIST


def test_valid_https_context() -> None:
    raw = '{"@context": "https://schema.org/", "name": "test"}'
    validate_jsonld_context(raw)  # Should not raise


def test_valid_http_context() -> None:
    raw = '{"@context": "http://schema.org/", "name": "test"}'
    validate_jsonld_context(raw)  # Should not raise


def test_valid_context_without_trailing_slash() -> None:
    raw = '{"@context": "https://schema.org", "name": "test"}'
    validate_jsonld_context(raw)  # Should not raise


def test_valid_bioschemas_context() -> None:
    raw = '{"@context": "https://bioschemas.org/", "name": "test"}'
    validate_jsonld_context(raw)  # Should not raise


def test_valid_context_list_with_schemaorg_and_extension() -> None:
    raw = '{"@context": ["https://schema.org/", {"bios": "https://bioschemas.org/"}], "name": "test"}'
    validate_jsonld_context(raw)  # Should not raise


def test_valid_context_dict_with_schemaorg() -> None:
    raw = '{"@context": {"schema": "https://schema.org/"}, "name": "test"}'
    validate_jsonld_context(raw)  # Should not raise


def test_raises_on_missing_context() -> None:
    raw = '{"name": "test"}'
    with pytest.raises(JsonLdContextError, match="Missing @context"):
        validate_jsonld_context(raw)


def test_raises_on_unknown_context() -> None:
    raw = '{"@context": "https://unknown.example.org/", "name": "test"}'
    with pytest.raises(JsonLdContextError, match="Unsupported @context"):
        validate_jsonld_context(raw)


def test_raises_on_unknown_extension_in_list() -> None:
    raw = '{"@context": ["https://schema.org/", {"ext": "https://unknown.example.org/"}], "name": "test"}'
    with pytest.raises(JsonLdContextError, match="Unsupported @context"):
        validate_jsonld_context(raw)


def test_raises_on_empty_context_list() -> None:
    raw = '{"@context": [], "name": "test"}'
    with pytest.raises(JsonLdContextError, match="Empty @context list"):
        validate_jsonld_context(raw)


def test_raises_on_non_string_context_in_dict() -> None:
    raw = '{"@context": {"schema": 123}, "name": "test"}'
    with pytest.raises(JsonLdContextError, match="Non-string @context value"):
        validate_jsonld_context(raw)


def test_raises_on_invalid_json() -> None:
    raw = "not valid json{{{"
    with pytest.raises(JsonLdContextError, match="Invalid JSON"):
        validate_jsonld_context(raw)


def test_raises_on_non_object_json() -> None:
    raw = '"just a string"'
    with pytest.raises(JsonLdContextError, match="JSON-LD must be a JSON object or array"):
        validate_jsonld_context(raw)


def test_valid_top_level_array_of_objects() -> None:
    raw = (
        '[{"@context": "https://schema.org/", "@type": "Dataset", "name": "A"},'
        ' {"@context": "https://schema.org/", "@type": "Dataset", "name": "B"}]'
    )
    validate_jsonld_context(raw)


def test_raises_on_empty_top_level_array() -> None:
    with pytest.raises(JsonLdContextError, match="Empty JSON-LD array"):
        validate_jsonld_context("[]")


def test_valid_context_dict_with_jsonld_keywords() -> None:
    raw = '{"@context": {"@vocab": "https://schema.org/", "@language": "en", "@version": 1.1}, "name": "test"}'
    validate_jsonld_context(raw)


def test_valid_context_dict_with_nested_term_definition() -> None:
    raw = (
        '{"@context": {"schema": "https://schema.org/", "url": {"@id": "schema:url", "@type": "@id"}}, "name": "test"}'
    )
    validate_jsonld_context(raw)


def test_raises_on_unknown_import_in_context_dict() -> None:
    raw = '{"@context": {"@vocab": "https://schema.org/", "@import": "https://evil.example/ctx"}, "name": "test"}'
    with pytest.raises(JsonLdContextError, match="Unsupported @context"):
        validate_jsonld_context(raw)


def test_raises_on_unknown_nested_context_in_term_definition() -> None:
    raw = (
        '{"@context": {"@vocab": "https://schema.org/", "x": {"@context": "https://evil.example/ctx"}}, "name": "test"}'
    )
    with pytest.raises(JsonLdContextError, match="Unsupported @context"):
        validate_jsonld_context(raw)


def test_valid_import_of_allowlisted_context() -> None:
    raw = '{"@context": {"@vocab": "https://schema.org/", "@import": "https://bioschemas.org/"}, "name": "test"}'
    validate_jsonld_context(raw)


def test_raises_on_context_type_not_supported() -> None:
    raw = '{"@context": 123, "name": "test"}'
    with pytest.raises(JsonLdContextError, match="Unsupported @context type"):
        validate_jsonld_context(raw)
