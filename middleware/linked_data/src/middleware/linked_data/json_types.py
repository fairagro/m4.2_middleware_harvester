"""JSON value typing for Linked Data discovery payloads.

Dict values use ``object`` (not nested ``JsonValue``) so that after
``isinstance(..., dict)`` mypy narrows to ``dict[str, object]`` without
invariance conflicts against discovery/mapper APIs.
"""

type JsonValue = dict[str, object] | list[JsonValue] | str | int | float | bool | None
