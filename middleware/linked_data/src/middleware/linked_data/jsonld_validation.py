"""JSON-LD @context validation — re-exported from ``middleware.generic``."""

from middleware.generic.jsonld_validation import (
    SCHEMAORG_CONTEXT_ALLOWLIST,
    JsonLdContextError,
    validate_jsonld_context,
    validate_jsonld_context_data,
)

__all__ = [
    "SCHEMAORG_CONTEXT_ALLOWLIST",
    "JsonLdContextError",
    "validate_jsonld_context",
    "validate_jsonld_context_data",
]
