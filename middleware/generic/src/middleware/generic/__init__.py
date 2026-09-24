"""Generic harvest plugin: Protocol + shared PayloadParser composition."""

from middleware.generic.config import Config, ProtocolType
from middleware.parsing import DiscoveryResult, JsonLdDiscoveryResult, ParserType, UrlDiscoveryResult

__all__ = [
    "Config",
    "DiscoveryResult",
    "JsonLdDiscoveryResult",
    "ParserType",
    "ProtocolType",
    "UrlDiscoveryResult",
]
