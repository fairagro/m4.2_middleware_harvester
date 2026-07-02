"""JSON-LD value types for Schema.org dataset extraction."""

from __future__ import annotations

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type SchemaOrgDatasetDict = dict[str, JsonValue]
