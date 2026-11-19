"""Unit tests for ``middleware.payload.geo``."""

from __future__ import annotations

import pytest

from middleware.payload.geo import bounding_box


@pytest.mark.parametrize(
    ("west", "south", "east", "north", "expected"),
    [
        (10.0, 48.0, 11.0, 49.0, "48.0 10.0 49.0 11.0"),
        ("6.9895", "50.6152", "6.9922", "50.6165", "50.6152 6.9895 50.6165 6.9922"),
        (10.0, 48.0, 11.0, None, None),
        ("", 48.0, 11.0, 49.0, None),
        ("x", 48.0, 11.0, 49.0, None),
        (None, None, None, None, None),
    ],
)
def test_bounding_box(
    west: float | str | None,
    south: float | str | None,
    east: float | str | None,
    north: float | str | None,
    expected: str | None,
) -> None:
    assert bounding_box(west, south, east, north) == expected
