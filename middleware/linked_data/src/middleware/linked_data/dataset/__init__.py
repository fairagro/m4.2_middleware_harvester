"""Dataset abstractions and implementations."""

from .dataset import (
    Dataset,
    DiscoveryResult,
    JsonLdDiscoveryResult,
    UrlDiscoveryResult,
)
from .html_jsonld import HtmlJsonLdDataset
from .regal_jsonld import RegalJsonLdDataset

__all__ = [
    "Dataset",
    "DiscoveryResult",
    "HtmlJsonLdDataset",
    "JsonLdDiscoveryResult",
    "RegalJsonLdDataset",
    "UrlDiscoveryResult",
]
