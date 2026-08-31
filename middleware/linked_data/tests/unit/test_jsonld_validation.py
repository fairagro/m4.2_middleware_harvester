"""JSON-LD @context validation unit tests."""

import pytest

from middleware.linked_data.jsonld_validation import (
    SCHEMAORG_CONTEXT_ALLOWLIST,
    JsonLdContextError,
    validate_jsonld_context,
)


class TestSchemaorgContextAllowlist:
    """Tests for the SCHEMAORG_CONTEXT_ALLOWLIST constant."""

    def test_allowlist_contains_schemaorg_https(self) -> None:
        assert "https://schema.org/" in SCHEMAORG_CONTEXT_ALLOWLIST

    def test_allowlist_contains_schemaorg_http(self) -> None:
        assert "http://schema.org/" in SCHEMAORG_CONTEXT_ALLOWLIST

    def test_allowlist_contains_schemaorg_without_trailing_slash(self) -> None:
        assert "https://schema.org" in SCHEMAORG_CONTEXT_ALLOWLIST

    def test_allowlist_contains_bioschemas(self) -> None:
        assert "https://bioschemas.org/" in SCHEMAORG_CONTEXT_ALLOWLIST


class TestValidateJsonLdContext:
    """Tests for validate_jsonld_context function."""

    def test_valid_https_context(self) -> None:
        raw = '{"@context": "https://schema.org/", "name": "test"}'
        validate_jsonld_context(raw)  # Should not raise

    def test_valid_http_context(self) -> None:
        raw = '{"@context": "http://schema.org/", "name": "test"}'
        validate_jsonld_context(raw)  # Should not raise

    def test_valid_context_without_trailing_slash(self) -> None:
        raw = '{"@context": "https://schema.org", "name": "test"}'
        validate_jsonld_context(raw)  # Should not raise

    def test_valid_bioschemas_context(self) -> None:
        raw = '{"@context": "https://bioschemas.org/", "name": "test"}'
        validate_jsonld_context(raw)  # Should not raise

    def test_valid_context_list_with_schemaorg_and_extension(self) -> None:
        raw = '{"@context": ["https://schema.org/", {"bios": "https://bioschemas.org/"}], "name": "test"}'
        validate_jsonld_context(raw)  # Should not raise

    def test_valid_context_dict_with_schemaorg(self) -> None:
        raw = '{"@context": {"schema": "https://schema.org/"}, "name": "test"}'
        validate_jsonld_context(raw)  # Should not raise

    def test_raises_on_missing_context(self) -> None:
        raw = '{"name": "test"}'
        with pytest.raises(JsonLdContextError, match="Missing @context"):
            validate_jsonld_context(raw)

    def test_raises_on_unknown_context(self) -> None:
        raw = '{"@context": "https://unknown.example.org/", "name": "test"}'
        with pytest.raises(JsonLdContextError, match="Unsupported @context"):
            validate_jsonld_context(raw)

    def test_raises_on_unknown_extension_in_list(self) -> None:
        raw = '{"@context": ["https://schema.org/", {"ext": "https://unknown.example.org/"}], "name": "test"}'
        with pytest.raises(JsonLdContextError, match="Unsupported @context"):
            validate_jsonld_context(raw)

    def test_raises_on_empty_context_list(self) -> None:
        raw = '{"@context": [], "name": "test"}'
        with pytest.raises(JsonLdContextError, match="Empty @context list"):
            validate_jsonld_context(raw)

    def test_raises_on_non_string_context_in_dict(self) -> None:
        raw = '{"@context": {"schema": 123}, "name": "test"}'
        with pytest.raises(JsonLdContextError, match="Non-string @context value"):
            validate_jsonld_context(raw)

    def test_raises_on_invalid_json(self) -> None:
        raw = "not valid json{{{"
        with pytest.raises(JsonLdContextError, match="Invalid JSON"):
            validate_jsonld_context(raw)

    def test_raises_on_non_object_json(self) -> None:
        raw = '"just a string"'
        with pytest.raises(JsonLdContextError, match="JSON-LD must be a JSON object"):
            validate_jsonld_context(raw)

    def test_raises_on_context_type_not_supported(self) -> None:
        raw = '{"@context": 123, "name": "test"}'
        with pytest.raises(JsonLdContextError, match="Unsupported @context type"):
            validate_jsonld_context(raw)
