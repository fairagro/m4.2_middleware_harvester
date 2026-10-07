"""Unit tests for nested ProtocolConfig (flat protocol fields removed)."""

from __future__ import annotations

import logging

import pytest
from pydantic import ValidationError

from middleware.contracts.nice_http_client import NiceHttpClientConfig
from middleware.generic.config import Config
from middleware.generic.protocol.protocol import ProtocolType


def test_nested_xml_protocol_config() -> None:
    cfg = Config.model_validate({
        "protocol": {
            "http": {"respect_robots_txt": False},
            "xml": {"entry_url": "https://example.org/sitemap.xml"},
        }
    })
    assert cfg.active_protocol_type is ProtocolType.xml
    assert cfg.effective_protocol.xml is not None
    assert cfg.effective_protocol.xml.entry_url == "https://example.org/sitemap.xml"
    assert cfg.effective_protocol.http.respect_robots_txt is False


def test_nested_mycore_solr_protocol_config() -> None:
    cfg = Config.model_validate({
        "protocol": {
            "mycore_solr": {
                "entry_url": "https://example.org/servlets/solr/select",
                "page_size": 50,
            }
        }
    })
    assert cfg.active_protocol_type is ProtocolType.mycore_solr
    assert cfg.effective_protocol.mycore_solr is not None
    assert cfg.effective_protocol.mycore_solr.page_size == 50


def test_protocol_rejects_zero_or_two_type_keys() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        Config.model_validate({"protocol": {"http": {}}})
    with pytest.raises(ValidationError, match="exactly one"):
        Config.model_validate({
            "protocol": {
                "xml": {"entry_url": "https://a.example/sitemap.xml"},
                "mycore_solr": {"entry_url": "https://b.example/select"},
            }
        })


def test_flat_protocol_fields_rejected() -> None:
    with pytest.raises(ValidationError, match="requires nested protocol"):
        Config.model_validate({
            "protocol_type": "mycore_solr",
            "sitemap_url": "https://example.org/servlets/solr/select",
            "page_size": 25,
            "http": {"respect_robots_txt": False},
        })


def test_missing_protocol_fails_closed() -> None:
    with pytest.raises(ValidationError, match="requires nested protocol"):
        Config.model_validate({"worker_tasks": 2})


def test_effective_resource_base_url_from_entry() -> None:
    cfg = Config.model_validate({
        "protocol": {"xml": {"entry_url": "https://host.example/path/sitemap.xml"}},
    })
    assert cfg.effective_resource_base_url == "https://host.example/resource/"


def test_http_default_on_protocol() -> None:
    cfg = Config.model_validate({
        "protocol": {"xml": {"entry_url": "https://example.org/sitemap.xml"}},
    })
    assert isinstance(cfg.effective_protocol.http, NiceHttpClientConfig)


def test_deprecated_threshold_warns_with_nested_protocol(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        Config.model_validate({
            "protocol": {"xml": {"entry_url": "https://example.org/sitemap.xml"}},
            "jsonld_parse_threshold_bytes": 1024,
        })
    assert any("jsonld_parse_threshold_bytes is deprecated" in record.message for record in caplog.records)
