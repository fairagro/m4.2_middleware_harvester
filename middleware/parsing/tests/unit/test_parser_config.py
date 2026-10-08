"""Unit tests for ParserConfig allowed_context_url."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from middleware.parsing.parser_config import HtmlJsonldParserConfig, JsonldParserConfig, ParserConfig
from middleware.parsing.parser_type import ParserType


def test_allowed_context_url_optional(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="middleware.parsing.parser_config"):
        cfg = ParserConfig(jsonld=JsonldParserConfig())
    assert cfg.allowed_context_url is None
    assert any("allowed_context_url is unset" in r.message for r in caplog.records)


def test_allowed_context_url_accepts_https(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="middleware.parsing.parser_config"):
        # YAML may supply a single string; coerce via model_validate (not __init__).
        cfg = ParserConfig.model_validate({
            "html_jsonld": {"allowed_context_url": "https://schema.org/"},
        })
    assert cfg.allowed_context_url == ["https://schema.org/"]
    assert not any("allowed_context_url is unset" in r.message for r in caplog.records)


def test_allowed_context_url_accepts_list() -> None:
    cfg = ParserConfig(
        html_jsonld=HtmlJsonldParserConfig(
            allowed_context_url=["https://schema.org/", "https://bioschemas.org/"],
        ),
    )
    assert cfg.allowed_context_url == ["https://schema.org/", "https://bioschemas.org/"]


def test_allowed_context_url_rejects_non_http() -> None:
    with pytest.raises(ValidationError, match="http"):
        ParserConfig.model_validate({
            "jsonld": {"allowed_context_url": "ftp://example.org/ctx"},
        })


def test_allowed_context_url_rejects_hostless_https() -> None:
    with pytest.raises(ValidationError, match="absolute http"):
        ParserConfig.model_validate({
            "jsonld": {"allowed_context_url": "https://"},
        })


def test_parser_config_type_as_key_nested(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="middleware.parsing.parser_config"):
        cfg = ParserConfig.model_validate({
            "html_jsonld": {"allowed_context_url": "https://schema.org/"},
        })
    assert cfg.type == ParserType.html_jsonld
    assert cfg.allowed_context_url == ["https://schema.org/"]
    assert not any("parser.type is deprecated" in r.message for r in caplog.records)


def test_parser_config_legacy_type_warns_and_lifts(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="middleware.parsing.parser_config"):
        cfg = ParserConfig.model_validate({
            "type": ParserType.jsonld,
            "allowed_context_url": "https://schema.org/",
        })
    assert cfg.type == ParserType.jsonld
    assert cfg.jsonld is not None
    assert cfg.allowed_context_url == ["https://schema.org/"]
    assert any("parser.type is deprecated" in r.message for r in caplog.records)


def test_parser_config_rejects_two_type_keys() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        ParserConfig.model_validate({"html_jsonld": {}, "jsonld": {}})
