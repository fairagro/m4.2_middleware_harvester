"""Shared helpers for GeneralSchemaOrgMapper unit tests."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from arctrl import ARC  # type: ignore[import-untyped]
from rdflib import Graph

from middleware.harvester.plugin_base import HarvestedArc
from middleware.linked_data.linked_data_mapper import MappingContext

BLANK_NODE_ID = re.compile(r"^N[0-9a-fA-F]{32}$")

# Explicit empty discovery context for unit tests that only exercise graph mapping.
NO_DISCOVERY = MappingContext()


def first_harvest(result: Iterable[HarvestedArc]) -> HarvestedArc:
    """Return the first HarvestedArc from an iterable, asserting exactly one."""
    items = list(result)
    assert len(items) == 1, f"Expected exactly one HarvestedArc, got {len(items)}"
    return items[0]


def assert_harvest_has_no_bnode_labels(arc_json: str) -> None:
    """Fail if ARC JSON embeds rdflib blank-node labels anywhere in the payload."""

    def is_bnode_label(value: str) -> bool:
        return bool(BLANK_NODE_ID.fullmatch(value) or value.startswith("_:"))

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


OPENAGRAR_PROPERTYVALUE_DOI = """
{
  "@context": "https://schema.org/",
  "@type": "Dataset",
  "name": "Flower visitors in legume-intercrops",
  "identifier": [{
    "@type": "PropertyValue",
    "propertyID": "https://registry.identifiers.org/registry/doi",
    "value": "10.3220/253-2025-42"
  }]
}
"""

OPENAGRAR_DUAL_DOI_TEMPLATE = """
{{
  "@context": "https://schema.org/",
  "@type": "Dataset",
  "name": "EmiDaT dual DOI example",
  "identifier": [
    {{
      "@type": "PropertyValue",
      "propertyID": "https://registry.identifiers.org/registry/doi",
      "value": "{first_doi}"
    }},
    {{
      "@type": "PropertyValue",
      "propertyID": "https://registry.identifiers.org/registry/doi",
      "value": "{second_doi}"
    }}
  ]
}}
"""


def parse_jsonld(payload: str) -> Graph:
    graph = Graph()
    graph.parse(data=payload, format="json-ld")
    return graph


def root_identifier(arc_json: str) -> str:
    assert_harvest_has_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    root = next(item for item in payload["@graph"] if item.get("@id") == "./")
    identifier = root["identifier"]
    assert isinstance(identifier, str)
    return identifier


def rocrate_prop(item: dict, short_name: str) -> str:
    """Read a compact or schema.org-expanded RO-Crate property from a @graph node."""
    value = item.get(short_name)
    if value is None:
        value = item.get(f"http://schema.org/{short_name}")
    if value is None:
        value = item.get(f"https://schema.org/{short_name}")
    return str(value) if value is not None else ""


def keywords_comment_text(arc_json: str) -> str | None:
    assert_harvest_has_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Comment" not in type_list:
            continue
        if rocrate_prop(item, "name") == "Keywords":
            return rocrate_prop(item, "text")
    return None


def keywords_derived_ids(arc_json: str) -> list[str]:
    """Return sorted @ids of Keywords Comment / ParameterValue nodes (hash-relevant)."""
    assert_harvest_has_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    ids: list[str] = []
    for item in payload.get("@graph", []):
        node_id = str(item.get("@id") or "")
        if "Keywords" in node_id and node_id.startswith(("#LDComment_Keywords", "#ParameterValue_Keywords")):
            ids.append(node_id)
    return sorted(ids)


def investigation_description(arc_json: str) -> str:
    assert_harvest_has_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Investigation" in type_list or "Dataset" in type_list:
            desc = rocrate_prop(item, "description")
            if desc:
                return desc
    for item in payload.get("@graph", []):
        if item.get("@type") in (None, "Comment"):
            continue
        desc = rocrate_prop(item, "description")
        if desc:
            return desc
    return ""


def contact_name_pairs(arc_json: str) -> list[tuple[str, str]]:
    """Return Investigation contact order from ARCtrl, not JSON-LD @graph order."""
    assert_harvest_has_no_bnode_labels(arc_json)
    arc = ARC.from_rocrate_json_string(arc_json)
    pairs: list[tuple[str, str]] = []
    for person in arc.Contacts:
        given = str(person.FirstName or "").strip()
        family = str(person.LastName or "").strip()
        if given or family:
            pairs.append((given, family))
    return pairs


def publication_author_node_id(arc_json: str) -> str | None:
    """Return a stable #Author_* @id (lexicographically smallest; @graph order is undefined)."""
    assert_harvest_has_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    author_ids = [
        person_id
        for item in payload.get("@graph", [])
        if (person_id := str(item.get("@id") or "")).startswith("#Author_")
    ]
    return min(author_ids) if author_ids else None


def assert_stable_author_node_id(author_id: str | None, expected_authors: str) -> None:
    """Match spec: @id is #Author_* and contains the author string; no Last, F. commas."""
    assert author_id is not None
    assert author_id.startswith("#Author_")
    assert expected_authors in author_id
    assert "," not in author_id


def publisher_comment_text(arc_json: str) -> str | None:
    assert_harvest_has_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Comment" not in type_list:
            continue
        if rocrate_prop(item, "name") == "Publisher":
            return rocrate_prop(item, "text")
    return None


def distribution_comment_texts(arc_json: str) -> list[str]:
    """Return Distribution Investigation Comment texts in @graph encounter order."""
    assert_harvest_has_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    texts: list[str] = []
    for item in payload.get("@graph", []):
        types = item.get("@type")
        type_list = types if isinstance(types, list) else [types]
        if "Comment" not in type_list:
            continue
        if rocrate_prop(item, "name") == "Distribution":
            texts.append(rocrate_prop(item, "text"))
    return texts


def dual_doi_payload(first_doi: str, second_doi: str) -> str:
    return OPENAGRAR_DUAL_DOI_TEMPLATE.format(first_doi=first_doi, second_doi=second_doi)


def alternate_identifier_values(arc_json: str) -> list[str]:
    assert_harvest_has_no_bnode_labels(arc_json)
    payload = json.loads(arc_json)
    values: list[str] = []
    for item in payload["@graph"]:
        if item.get("@type") == "Comment" and item.get("name") == "Alternate Identifier":
            text = item.get("text")
            if isinstance(text, str):
                values.append(text)
    return values


def pangaea_doi_graph(doi: str = "10.1594/PANGAEA.957630") -> Graph:
    return parse_jsonld(
        f"""
        {{
          "@context": "https://schema.org/",
          "@type": "Dataset",
          "name": "Shared PANGAEA DOI",
          "identifier": [{{
            "@type": "PropertyValue",
            "propertyID": "https://registry.identifiers.org/registry/doi",
            "value": "{doi}"
          }}]
        }}
        """
    )
