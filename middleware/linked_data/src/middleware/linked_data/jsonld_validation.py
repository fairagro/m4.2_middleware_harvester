"""JSON-LD @context validation for Schema.org sources."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

# Known Schema.org contexts (http and https variants)
_SCHEMAORG_CONTEXTS: frozenset[str] = frozenset(
    {
        "https://schema.org/",
        "http://schema.org/",
        "https://schema.org",
        "http://schema.org",
    }
)

# Known extension contexts that are acceptable alongside Schema.org
_KNOWN_EXTENSION_CONTEXTS: frozenset[str] = frozenset(
    {
        "https://bioschemas.org/",
        "http://bioschemas.org/",
        "https://bioschemas.org",
        "http://bioschemas.org",
    }
)

# Combined allowlist: Schema.org + known extensions
SCHEMAORG_CONTEXT_ALLOWLIST: frozenset[str] = _SCHEMAORG_CONTEXTS | _KNOWN_EXTENSION_CONTEXTS


class JsonLdContextError(Exception):
    """Raised when JSON-LD @context is not in the allowlist."""


def validate_jsonld_context(raw_json: str) -> None:
    """Validate that JSON-LD @context is Schema.org or a known extension.

    Accepts a single JSON object or a top-level array of objects (common for
    embedded HTML JSON-LD). Each document must carry an allowlisted ``@context``.

    Parameters
    ----------
    raw_json : str
        Raw JSON-LD string to validate.

    Raises
    ------
    JsonLdContextError
        If @context is missing, empty, or contains unknown contexts.
    """
    try:
        data: Any = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise JsonLdContextError(f"Invalid JSON: {exc}") from exc

    if isinstance(data, list):
        if not data:
            raise JsonLdContextError("Empty JSON-LD array")
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise JsonLdContextError(f"JSON-LD array item {index} must be a JSON object, got {type(item).__name__}")
            _validate_document_context(item)
        return

    if not isinstance(data, dict):
        raise JsonLdContextError("JSON-LD must be a JSON object or array of objects")

    _validate_document_context(data)


def _validate_document_context(data: dict[str, Any]) -> None:
    """Validate ``@context`` on one JSON-LD document object."""
    context = data.get("@context")
    if context is None:
        raise JsonLdContextError("Missing @context in JSON-LD payload")
    _validate_context_value(context)


def _validate_context_value(context: Any) -> None:
    """Validate a single @context value (string, list, or dict)."""
    if isinstance(context, str):
        _check_context_string(context)
    elif isinstance(context, list):
        _validate_context_list(context)
    elif isinstance(context, dict):
        _validate_context_dict(context)
    else:
        raise JsonLdContextError(f"Unsupported @context type: {type(context).__name__}")


def _validate_context_list(contexts: Sequence[Any]) -> None:
    """Validate a list @context (e.g., ["https://schema.org/", {...}])."""
    if not contexts:
        raise JsonLdContextError("Empty @context list")

    for item in contexts:
        _validate_context_value(item)


def _validate_context_dict(contexts: dict[str, Any]) -> None:
    """Validate a dict @context, checking only remote vocabulary IRIs.

    JSON-LD keywords (``@language``, ``@version``, …) may carry non-URI values.
    Absolute ``http(s)`` strings (including ``@vocab``) must be allowlisted.
    Nested term definitions (dicts) are accepted without further checks.
    """
    for key, value in contexts.items():
        if key.startswith("@") and key != "@vocab":
            continue
        _validate_context_entry_value(key, value)


def _validate_context_entry_value(key: str, value: Any) -> None:
    """Allowlist absolute http(s) IRIs; ignore local term definitions."""
    if isinstance(value, str):
        if value.startswith(("http://", "https://")):
            _check_context_string(value)
        return
    if isinstance(value, dict):
        # Term definition object (e.g. {"@id": "...", "@type": "@id"}).
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.startswith(("http://", "https://")):
                _check_context_string(item)
            elif isinstance(item, dict):
                continue
            elif not isinstance(item, str):
                raise JsonLdContextError(f"Unsupported @context list item for '{key}': {type(item).__name__}")
        return
    raise JsonLdContextError(f"Non-string @context value for prefix '{key}': {type(value).__name__}")


def _check_context_string(context: str) -> None:
    """Check if a single context string is in the allowlist."""
    normalized = context.strip()
    if normalized not in SCHEMAORG_CONTEXT_ALLOWLIST:
        raise JsonLdContextError(f"Unsupported @context: {normalized}")
