"""Unit tests for shared display-name splitting."""

from __future__ import annotations

import pytest

from middleware.linked_data.linked_data_mapper.person_names import PersonNameParts, split_display_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Ada Lovelace", PersonNameParts(given="Ada", family="Lovelace")),
        (
            "Dr. Juan Q. Xavier de la Vega III",
            PersonNameParts(given="Juan Q. Xavier", family="de la Vega"),
        ),
        ("van der Berg, Johannes", PersonNameParts(given="Johannes", family="van der Berg")),
        ("Lovelace, Ada", PersonNameParts(given="Ada", family="Lovelace")),
        ("Hans-Peter Müller", PersonNameParts(given="Hans-Peter", family="Müller")),
        ("Mary Ann Smith", PersonNameParts(given="Mary Ann", family="Smith")),
        ("Johannes van der Berg", PersonNameParts(given="Johannes", family="van der Berg")),
        # Single token → unlabeled agent (fail-closed Person policy)
        ("Zenodo", PersonNameParts(given=None, family="Zenodo")),
        ("", PersonNameParts(given=None, family="")),
        ("   ", PersonNameParts(given=None, family="")),
    ],
)
def test_split_display_name(raw: str, expected: PersonNameParts) -> None:
    assert split_display_name(raw) == expected


def test_split_display_name_is_deterministic() -> None:
    sample = "Dr. Juan Q. Xavier de la Vega III"
    assert split_display_name(sample) == split_display_name(sample)
