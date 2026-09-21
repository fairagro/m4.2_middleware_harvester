"""Dataset abstractions and implementations.

Concrete dataset classes are imported from their modules (e.g.
``dataset.html_jsonld``) so infrastructure code can import discovery types
without loading provider implementations.
"""

from middleware.generic.discovery import DiscoveryResult, JsonLdDiscoveryResult, UrlDiscoveryResult
from middleware.linked_data.dataset.dataset import Dataset

__all__ = [
    "Dataset",
    "DiscoveryResult",
    "JsonLdDiscoveryResult",
    "UrlDiscoveryResult",
]
