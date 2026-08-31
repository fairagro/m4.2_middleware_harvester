"""Unit tests for mapper_test_helpers blank-node assertions."""

from __future__ import annotations

import json

import pytest
from mapper_test_helpers import assert_harvest_has_no_bnode_labels


def test_assert_harvest_has_no_bnode_labels_passes_clean_payload() -> None:
    assert_harvest_has_no_bnode_labels(
        json.dumps({"@graph": [{"@id": "./", "identifier": "example_org_ds", "name": "ok"}]})
    )


def test_assert_harvest_has_no_bnode_labels_fails_on_nested_comment_text() -> None:
    payload = {
        "@graph": [
            {
                "@id": "./",
                "comment": [{"@type": "Comment", "name": "Publisher", "text": "N" + ("a" * 32)}],
            }
        ]
    }
    with pytest.raises(AssertionError, match=r"blank-node label at"):
        assert_harvest_has_no_bnode_labels(json.dumps(payload))


def test_assert_harvest_has_no_bnode_labels_fails_on_underscore_colon_label() -> None:
    with pytest.raises(AssertionError, match=r"blank-node label at"):
        assert_harvest_has_no_bnode_labels(json.dumps({"@graph": [{"identifier": "_:b0"}]}))
