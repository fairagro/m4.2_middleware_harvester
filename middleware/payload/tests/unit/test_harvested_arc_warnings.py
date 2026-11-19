"""HarvestedArc.warnings transport (issue #637)."""

from __future__ import annotations

from arctrl import ARC, ArcInvestigation  # type: ignore[import-untyped]

from middleware.payload.harvested_arc import HarvestedArc


def _minimal_arc() -> ARC:
    return ARC.from_arc_investigation(ArcInvestigation.create(identifier="warn-id", title="Warn Title"))


def test_from_arctrl_default_warnings_empty() -> None:
    harvested = HarvestedArc.from_arctrl(_minimal_arc())

    assert not harvested.warnings
    assert harvested.identifier == "warn-id"


def test_from_arctrl_preserves_warnings_without_changing_json() -> None:
    # One from_arctrl call: ARCtrl stamps serialisation time, so two calls diverge in JSON.
    warned = HarvestedArc.from_arctrl(
        _minimal_arc(),
        source_url="https://example.org/d1",
        warnings=("title fallback: headline", "unparsed datePublished"),
    )

    assert warned.warnings == ("title fallback: headline", "unparsed datePublished")
    assert warned.identifier == "warn-id"
    assert warned.source_url == "https://example.org/d1"
    assert warned.studies >= 0
    assert warned.assays >= 0
    assert '"name":"Warn Title"' in warned.arc_json or "Warn Title" in warned.arc_json
