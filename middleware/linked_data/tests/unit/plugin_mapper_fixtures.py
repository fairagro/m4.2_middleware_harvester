"""Fixtures/helpers for linked_data plugin tests that touch mapper ARC JSON.

Kept local (not ``mapper_test_helpers``) so pytest ``pythonpath`` order cannot
shadow ``middleware/payload/tests/unit/mapper_test_helpers.py``, and the IDE can
resolve a same-package import without product paths in synced pyrightconfig.
"""

from __future__ import annotations

import json
import re

from rdflib import Graph

_BLANK_NODE_ID = re.compile(r"^N[0-9a-fA-F]{32}$")

# OpenAgrar shape: schema:name missing; title only via page html_title fallback.
OPENAGRAR_MISSING_NAME_NO_FALLBACK = """
{
  "@context": "https://schema.org/",
  "@type": "Dataset",
  "identifier": [{
    "@type": "PropertyValue",
    "propertyID": "https://registry.identifiers.org/registry/doi",
    "value": "10.3220/253-2025-42"
  }]
}
"""


def parse_jsonld(payload: str) -> Graph:
    graph = Graph()
    graph.parse(data=payload, format="json-ld")
    return graph


def _assert_no_bnode_labels(arc_json: str) -> None:
    def is_bnode_label(value: str) -> bool:
        return bool(_BLANK_NODE_ID.fullmatch(value) or value.startswith("_:"))

    def walk(value: object, path: str) -> None:
        if isinstance(value, str):
            if is_bnode_label(value):
                raise AssertionError(f"blank-node label at {path}: {value}")
            return
        if isinstance(value, dict):
            for key, inner in value.items():
                walk(inner, f"{path}.{key}")
            return
        if isinstance(value, list):
            for idx, inner in enumerate(value):
                walk(inner, f"{path}[{idx}]")

    walk(json.loads(arc_json), "$")


def _rocrate_prop(item: dict, short_name: str) -> str:
    value = item.get(short_name)
    if value is None:
        value = item.get(f"http://schema.org/{short_name}")
    if value is None:
        value = item.get(f"https://schema.org/{short_name}")
    return str(value) if value is not None else ""


def root_title(arc_json: str) -> str:
    _assert_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    root = next(item for item in payload["@graph"] if item.get("@id") == "./")
    return _rocrate_prop(root, "name")


def title_source_comment_text(arc_json: str) -> str | None:
    _assert_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Comment" not in type_list:
            continue
        if _rocrate_prop(item, "name") == "Title Source":
            return _rocrate_prop(item, "text")
    return None
