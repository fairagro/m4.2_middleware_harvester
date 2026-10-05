"""RDI placeholder values (#413)."""

from __future__ import annotations

import pytest

from middleware.payload.placeholders import is_placeholder, normalize_placeholder_values


@pytest.mark.parametrize(
    "value",
    [
        "None",
        "  none ",
        "NULL",
        "n/a",
        "No abstract provided",
        "Keine Zusammenfassung vorhanden",
        "No information provided",
        "$licenseURL",
        "${licenseURL}",
        "{{ license_url }}",
    ],
)
def test_is_placeholder(value: str) -> None:
    assert is_placeholder(value)


@pytest.mark.parametrize(
    "value",
    ["", "None of the plots were irrigated.", "Not Specified: The original author did not specify a license.", "$5"],
)
def test_is_not_placeholder(value: str) -> None:
    assert not is_placeholder(value)


def test_custom_values_are_folded() -> None:
    values = normalize_placeholder_values([" Keine Angabe ", ""])

    assert values == frozenset({"keine angabe"})
    assert is_placeholder("KEINE ANGABE", values)
    assert not is_placeholder("None", values)
