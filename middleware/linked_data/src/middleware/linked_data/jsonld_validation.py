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
    validate_jsonld_context_data(data)


def validate_jsonld_context_data(data: Any) -> None:
    """Validate ``@context`` on already-parsed JSON (object or array of objects).

    Prefer this over :func:`validate_jsonld_context` when the caller has already
    decoded the payload (e.g. HTML block normalization) to avoid a second
    ``json.loads``.
    """
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
    """Validate a dict @context, checking remote vocabulary / import IRIs.

    Absolute ``http(s)`` ``@vocab`` values must be allowlisted; relative ``@vocab``
    is allowed (IRI expansion only, no remote load). ``@import`` must be an
    absolute allowlisted ``http(s)`` IRI — relative or other schemes are rejected
    so processors cannot resolve them against a document base. Nested term
    definitions are scanned for nested ``@context`` / ``@import`` only — other
    keys (``@id``, ``@type``, ``@language``, …) are ignored.
    """
    for key, value in contexts.items():
        if key == "@vocab":
            _validate_vocab_ref(value)
            continue
        if key == "@import":
            _validate_import_ref(value)
            continue
        if key.startswith("@"):
            continue
        _validate_context_entry_value(key, value)


def _validate_vocab_ref(value: Any) -> None:
    """Allowlist absolute http(s) @vocab; permit relative / other non-HTTP strings."""
    if isinstance(value, str):
        http_iri = _normalized_http_context_iri(value)
        if http_iri is not None:
            _check_allowlisted_context_iri(http_iri)
        return
    if isinstance(value, list):
        for item in value:
            _validate_vocab_ref(item)
        return
    raise JsonLdContextError(f"Unsupported @vocab reference type: {type(value).__name__}")


def _validate_import_ref(value: Any) -> None:
    """Require absolute allowlisted http(s) @import (no relative / other schemes)."""
    if isinstance(value, str):
        http_iri = _normalized_http_context_iri(value)
        if http_iri is None:
            raise JsonLdContextError(f"Unsupported @import (must be absolute http(s) IRI): {value.strip()}")
        _check_allowlisted_context_iri(http_iri)
        return
    if isinstance(value, list):
        for item in value:
            _validate_import_ref(item)
        return
    raise JsonLdContextError(f"Unsupported @import reference type: {type(value).__name__}")


def _validate_context_entry_value(key: str, value: Any) -> None:
    """Allowlist absolute http(s) IRIs; scan nested term defs for remote contexts."""
    if isinstance(value, str):
        http_iri = _normalized_http_context_iri(value)
        if http_iri is not None:
            _check_allowlisted_context_iri(http_iri)
        return
    if isinstance(value, dict):
        _validate_nested_term_definition(value)
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                http_iri = _normalized_http_context_iri(item)
                if http_iri is not None:
                    _check_allowlisted_context_iri(http_iri)
            elif isinstance(item, dict):
                _validate_nested_term_definition(item)
            elif not isinstance(item, str):
                raise JsonLdContextError(f"Unsupported @context list item for '{key}': {type(item).__name__}")
        return
    raise JsonLdContextError(f"Non-string @context value for prefix '{key}': {type(value).__name__}")


def _validate_nested_term_definition(term_def: dict[str, Any]) -> None:
    """Reject remote context loads hidden inside a term definition object."""
    if "@context" in term_def:
        _validate_context_value(term_def["@context"])
    if "@import" in term_def:
        _validate_import_ref(term_def["@import"])


def _normalized_http_context_iri(value: str) -> str | None:
    """Return stripped IRI with lowercase http(s) scheme, or None if not absolute http(s).

    Leading/trailing whitespace is stripped. Scheme matching is case-insensitive
    (``HTTPS://…`` → ``https://…``). Protocol-relative (``//…``), ``file:``, and
    other schemes return ``None``.
    """
    stripped = value.strip()
    folded = stripped.casefold()
    for scheme in ("https://", "http://"):
        if folded.startswith(scheme):
            return f"{scheme}{stripped[len(scheme) :]}"
    return None


def _check_context_string(context: str) -> None:
    """Check if a single context string is an allowlisted absolute http(s) IRI."""
    http_iri = _normalized_http_context_iri(context)
    if http_iri is None:
        raise JsonLdContextError(f"Unsupported @context: {context.strip()}")
    _check_allowlisted_context_iri(http_iri)


def _check_allowlisted_context_iri(http_iri: str) -> None:
    """Require ``http_iri`` to be an exact allowlist member (already normalized)."""
    if http_iri not in SCHEMAORG_CONTEXT_ALLOWLIST:
        raise JsonLdContextError(f"Unsupported @context: {http_iri}")
