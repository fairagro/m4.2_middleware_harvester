"""Unit tests for ParserConfig allowed_context_url."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from middleware.parsing.parser_config import ParserConfig
from middleware.parsing.parser_type import ParserType


def test_allowed_context_url_optional(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="middleware.parsing.parser_config"):
        cfg = ParserConfig(type=ParserType.jsonld)
    assert cfg.allowed_context_url is None
    assert any("allowed_context_url is unset" in r.message for r in caplog.records)


def test_allowed_context_url_accepts_https(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="middleware.parsing.parser_config"):
        cfg = ParserConfig(type=ParserType.html_jsonld, allowed_context_url="https://schema.org/")
    assert cfg.allowed_context_url == "https://schema.org/"
    assert not any("allowed_context_url is unset" in r.message for r in caplog.records)


def test_allowed_context_url_rejects_non_http() -> None:
    with pytest.raises(ValidationError, match="http"):
        ParserConfig(type=ParserType.jsonld, allowed_context_url="ftp://example.org/ctx")


def test_allowed_context_url_rejects_hostless_https() -> None:
    with pytest.raises(ValidationError, match="absolute http"):
        ParserConfig(type=ParserType.jsonld, allowed_context_url="https://")
