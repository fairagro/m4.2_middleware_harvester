"""Shared discovery units and PayloadParser registry."""

from middleware.parsing.discovery import DiscoveryResult, JsonLdDiscoveryResult, UrlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_config import ParserConfig
from middleware.parsing.parser_type import ParserType

__all__ = [
    "DiscoveryResult",
    "JsonLdDiscoveryResult",
    "ParserConfig",
    "ParserError",
    "ParserType",
    "PayloadParser",
    "UrlDiscoveryResult",
]
