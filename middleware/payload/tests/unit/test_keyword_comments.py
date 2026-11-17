"""Unit tests for shared keyword Investigation Comment helper."""

from __future__ import annotations

from arctrl import ArcInvestigation  # type: ignore[import-untyped]

from middleware.payload.keyword_comments import KeywordClassification, KeywordSubject, add_keyword_comments


def _comments(inv: ArcInvestigation) -> dict[str, str]:
    return {c.Name: c.Value for c in inv.Comments if c.Name}


def test_plain_subjects_aggregate_and_per_term() -> None:
    inv = ArcInvestigation.create(identifier="i", title="t")
    add_keyword_comments(inv, subjects=[KeywordSubject("Soil"), KeywordSubject("Water")])
    comments = _comments(inv)
    assert comments["Keywords"] == "Soil, Water"
    assert comments["keyword [Soil]"] == "Soil"
    assert comments["keyword [Water]"] == "Water"


def test_casefold_dedupe_in_aggregate_and_plain_names() -> None:
    inv = ArcInvestigation.create(identifier="i", title="t")
    add_keyword_comments(inv, subjects=[("Soil", None), ("soil", None), ("Agriculture", None)])
    comments = _comments(inv)
    assert comments["Keywords"] == "Agriculture, Soil"
    assert "keyword [Soil]" in comments
    assert "keyword [soil]" not in comments
    assert comments["keyword [Agriculture]"] == "Agriculture"


def test_uri_term_uses_bracketed_uri() -> None:
    inv = ArcInvestigation.create(identifier="i", title="t")
    add_keyword_comments(
        inv,
        subjects=[KeywordSubject("aerosols", "http://example.org/agrovoc/c_1")],
    )
    comments = _comments(inv)
    assert comments["Keywords"] == "aerosols"
    assert comments["keyword [http://example.org/agrovoc/c_1]"] == "aerosols"


def test_ddc_with_uri_and_excluded_from_aggregate() -> None:
    inv = ArcInvestigation.create(identifier="i", title="t")
    add_keyword_comments(
        inv,
        subjects=[KeywordSubject("Soil")],
        classifications=[KeywordClassification("Landwirtschaft", "http://dewey.info/class/630/")],
    )
    comments = _comments(inv)
    assert comments["Keywords"] == "Soil"
    assert "Landwirtschaft" not in comments["Keywords"]
    assert comments["keyword [DDC:http://dewey.info/class/630/]"] == "Landwirtschaft"


def test_ddc_without_uri_omitted() -> None:
    inv = ArcInvestigation.create(identifier="i", title="t")
    add_keyword_comments(
        inv,
        subjects=[KeywordSubject("Soil")],
        classifications=[("Landwirtschaft", "")],
    )
    comments = _comments(inv)
    assert comments == {"Keywords": "Soil", "keyword [Soil]": "Soil"}


def test_empty_subjects_emit_nothing() -> None:
    inv = ArcInvestigation.create(identifier="i", title="t")
    add_keyword_comments(inv, subjects=[KeywordSubject("  "), ("", None)])
    assert inv.Comments == []
