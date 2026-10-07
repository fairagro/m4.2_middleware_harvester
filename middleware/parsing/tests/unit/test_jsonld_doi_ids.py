"""Bare-DOI JSON-LD ``@id`` values become ``https://doi.org/`` IRIs (#416)."""

from __future__ import annotations

from typing import Any

import pytest

from middleware.parsing.jsonld_doi_ids import doi_ids_as_iris


@pytest.mark.parametrize(
    ("node_id", "expected"),
    [
        ("10.5447/ipk/2011/0", "https://doi.org/10.5447/ipk/2011/0"),  # e!DAL Dataset @id
        (" 10.5447/IPK/2016/7 ", "https://doi.org/10.5447/IPK/2016/7"),
        ("https://doi.org/10.5447/ipk/2011/0", "https://doi.org/10.5447/ipk/2011/0"),
        ("https://example.org/dataset/1", "https://example.org/dataset/1"),
        ("10.5", "10.5"),  # not a DOI: left as it is
        ("#person_1", "#person_1"),
    ],
)
def test_node_id(node_id: str, expected: str) -> None:
    assert doi_ids_as_iris({"@id": node_id, "name": "x"}) == {"@id": expected, "name": "x"}


def test_nested_nodes_and_lists_are_rewritten_without_touching_values() -> None:
    document: dict[str, Any] = {
        "@context": "http://schema.org",
        "@graph": [{"@id": "10.1/a", "citation": {"@id": "10.2/b"}, "identifier": "10.3/c"}],
    }

    assert doi_ids_as_iris(document) == {
        "@context": "http://schema.org",
        "@graph": [
            {"@id": "https://doi.org/10.1/a", "citation": {"@id": "https://doi.org/10.2/b"}, "identifier": "10.3/c"}
        ],
    }
    assert document["@graph"][0]["@id"] == "10.1/a"  # input not mutated
