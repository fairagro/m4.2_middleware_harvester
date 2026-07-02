"""Helpers for extracting Schema.org Dataset objects from JSON-LD payloads."""

from __future__ import annotations

import json
from typing import cast

from .jsonld_types import JsonValue, SchemaOrgDatasetDict


class _MissingSentinel:
    """Sentinel for missing values during dot-path field resolution."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _MissingSentinel()
FieldResolutionState = JsonValue | _MissingSentinel


def _is_dataset_type(type_value: JsonValue) -> bool:
    if isinstance(type_value, str):
        return type_value == "Dataset" or type_value.endswith("/Dataset")
    if isinstance(type_value, list):
        return any(_is_dataset_type(item) for item in type_value)
    return False


def _find_dataset_object(obj: JsonValue) -> SchemaOrgDatasetDict | None:
    """Locate the first Schema.org Dataset dict inside a parsed JSON-LD value.

    JSON-LD on repository pages is not always a bare Dataset object. Common shapes:

    - A Dataset root: ``{"@type": "Dataset", ...}``
    - A named graph wrapper: ``{"@graph": [{"@type": "Dataset", ...}, ...]}``
    - A list of top-level objects (multiple script blocks merged upstream)

    The search is depth-first and returns the **first** object whose ``@type`` is
    ``Dataset`` or ends with ``/Dataset`` (compact or absolute IRI). Non-dataset
    nodes are skipped; nested ``@graph`` arrays and lists are walked recursively.
    """
    if isinstance(obj, dict):
        if _is_dataset_type(obj.get("@type")):
            return obj
        # JSON-LD containers often wrap entities in @graph instead of @type at root.
        graph = obj.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                found = _find_dataset_object(item)
                if found is not None:
                    return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_dataset_object(item)
            if found is not None:
                return found
    return None


def extract_schema_org_dataset_dict(jsonld_blocks: list[str]) -> SchemaOrgDatasetDict:
    """Return the first Schema.org Dataset object found across JSON-LD blocks."""
    for block in jsonld_blocks:
        parsed = cast(JsonValue, json.loads(block, strict=False))
        found = _find_dataset_object(parsed)
        if found is not None:
            return found
    raise ValueError("No Schema.org Dataset found in JSON-LD blocks")


def _coerce_final_value(value: JsonValue | _MissingSentinel) -> str | None:
    if value is _MISSING:
        return None
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    if value is None:
        return None
    return str(value)


def resolve_field_value(dataset_dict: SchemaOrgDatasetDict, field: str) -> str | None:
    """Resolve a dot-path field against a Schema.org Dataset dict."""
    current: FieldResolutionState = dataset_dict
    segments = field.split(".")

    for index, segment in enumerate(segments):
        if isinstance(current, list):
            current = current[0] if current else _MISSING
        if current is _MISSING:
            return None
        if not isinstance(current, dict):
            return None
        current = current.get(segment, _MISSING)
        if current is _MISSING:
            return None

        is_last = index == len(segments) - 1
        if not is_last and isinstance(current, list):
            current = current[0] if current else _MISSING

    return _coerce_final_value(current)
