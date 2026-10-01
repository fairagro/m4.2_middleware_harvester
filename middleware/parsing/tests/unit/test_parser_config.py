"""Unit tests for ParserConfig allowed_context_url."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from middleware.parsing.parser_config import ParserConfig
from middleware.parsing.parser_type import ParserType


def test_allowed_context_url_optional() -> None:
    cfg = ParserConfig(type=ParserType.jsonld)
    assert cfg.allowed_context_url is None


def test_allowed_context_url_accepts_https() -> None:
    cfg = ParserConfig(type=ParserType.html_jsonld, allowed_context_url="https://schema.org/")
    assert cfg.allowed_context_url == "https://schema.org/"


def test_allowed_context_url_rejects_non_http() -> None:
    with pytest.raises(ValidationError, match="http"):
        ParserConfig(type=ParserType.jsonld, allowed_context_url="ftp://example.org/ctx")
