"""Unit tests for shared discovery result types."""

from __future__ import annotations

from middleware.parsing.discovery import JsonLdDiscoveryResult, UrlDiscoveryResult


def test_jsonld_discovery_result_harvest_source_id_defaults_to_none() -> None:
    result = JsonLdDiscoveryResult(identifier="key", payload={"@id": "https://example.org/1"})
    assert result.harvest_source_id is None


def test_jsonld_discovery_result_accepts_explicit_harvest_source_id() -> None:
    result = JsonLdDiscoveryResult(
        identifier="key",
        payload={"@id": "https://example.org/1"},
        harvest_source_id="key",
    )
    assert result.harvest_source_id == "key"


def test_url_discovery_result_harvest_source_id_defaults_to_none() -> None:
    result = UrlDiscoveryResult("https://example.org/1")
    assert result.harvest_source_id is None
