"""Generic harvest plugin: Protocol + PayloadParser composition."""

from middleware.generic.config import Config, ParserType, ProtocolType
from middleware.generic.discovery import DiscoveryResult, JsonLdDiscoveryResult, UrlDiscoveryResult

__all__ = [
    "Config",
    "DiscoveryResult",
    "JsonLdDiscoveryResult",
    "ParserType",
    "ProtocolType",
    "UrlDiscoveryResult",
]
