"""Regression tests for arctrl / fable-library compatibility shims."""

from __future__ import annotations

from arctrl import ArcTable

from middleware.harvester.arctrl_compat import CompositeCell, CompositeHeader


def test_free_text_longer_than_200_chars_does_not_raise() -> None:
    """fable_library string_hash must tolerate long FreeText (DWD URL joins)."""
    table = ArcTable.init("Measurement")
    long_value = "https://example.invalid/" + ("a" * 250)
    assert len(long_value) > 200
    table.AddColumn(
        CompositeHeader.comment("Online Resource"),
        [CompositeCell.free_text(long_value)],
    )
    assert table.ColumnCount == 1
