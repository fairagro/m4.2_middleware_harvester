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

    Parameters
    ----------
    raw_json : str
        Raw JSON-LD string to validate.

    Raises
    ------
    JsonLdContextError
        If @context is missing, empty, or contains unknown contexts.

    Examples
    --------
    >>> validate_jsonld_context('{"@context": "https://schema.org/", "name": "test"}')
    >>> validate_jsonld_context('{"@context": ["https://schema.org/", {"bios": "https://bioschemas.org/"}]}')
    >>> validate_jsonld_context('{"@context": "https://unknown.example.org/"}')  # doctest: +SKIP
    Traceback (most recent call last):
        ...
    JsonLdContextError: Unsupported @context: https://unknown.example.org/
    """
    try:
        data: Any = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise JsonLdContextError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise JsonLdContextError("JSON-LD must be a JSON object")

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
    """Validate a dict @context (e.g., {"schema": "https://schema.org/"})."""
    for prefix, uri in contexts.items():
        if not isinstance(uri, str):
            raise JsonLdContextError(f"Non-string @context value for prefix '{prefix}': {type(uri).__name__}")
        _check_context_string(uri)


def _check_context_string(context: str) -> None:
    """Check if a single context string is in the allowlist."""
    normalized = context.strip()
    if normalized not in SCHEMAORG_CONTEXT_ALLOWLIST:
        raise JsonLdContextError(f"Unsupported @context: {normalized}")
