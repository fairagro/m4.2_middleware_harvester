"""Unique ARC comment names, so the API can ``ARC.Write`` every harvested ARC."""

from __future__ import annotations

import json
from pathlib import Path

from arctrl import ARC, ArcAssay, ArcInvestigation, ArcStudy, Comment, Person  # type: ignore[import-untyped]

from middleware.payload.arc_comments import drop_date_modified_comment_node, merge_duplicate_comments
from middleware.payload.arc_dates import date_modified_comment
from middleware.payload.harvested_arc import HarvestedArc


def _pairs(comments: list[Comment]) -> list[tuple[str, str | None]]:
    return [(c.Name, c.Value) for c in comments]


def test_same_name_comments_are_merged_in_order() -> None:
    comments = [
        Comment.create("associatedDataset", "frl:1"),
        Comment.create("License", "CC BY 4.0"),
        Comment.create("associatedDataset", "frl:2"),
        Comment.create("associatedDataset", "frl:1"),
    ]

    merge_duplicate_comments(comments)

    assert _pairs(comments) == [("associatedDataset", "frl:1; frl:2"), ("License", "CC BY 4.0")]


def _arc_with_duplicates() -> ARC:
    inv = ArcInvestigation.create(identifier="dup", title="Duplicates")
    inv.Comments.extend([Comment.create("a", "1"), Comment.create("a", "2")])
    person = Person.create(first_name="Ada", last_name="Lovelace")
    person.Comments.extend([Comment.create("p", "1"), Comment.create("p", "2")])
    inv.Contacts.append(person)
    study = ArcStudy.create("s")
    study.Comments.extend([Comment.create("s", "1"), Comment.create("s", "2")])
    inv.AddRegisteredStudy(study)
    assay = ArcAssay.create("a")
    assay.Comments.extend([Comment.create("x", "1"), Comment.create("x", "2")])
    inv.AddAssay(assay)
    inv.Comments.append(date_modified_comment("2024-09-04T09:34:30.938+0200"))
    return ARC.from_arc_investigation(inv)


def test_harvested_arc_survives_the_api_read_and_write(tmp_path: Path) -> None:
    """The API reads every harvested RO-Crate and writes it with ARC.Write, which fails on repeated names."""
    arc_json = HarvestedArc.from_arctrl(_arc_with_duplicates()).arc_json

    arc = ARC.from_rocrate_json_string(arc_json)
    arc.Write(str(tmp_path))

    assert _pairs(arc.Comments).count(("dateModified", "2024-09-04T09:34:30.938+0200")) == 1
    assert ("a", "1; 2") in _pairs(arc.Comments)
    assert _pairs(arc.Contacts[0].Comments) == [("p", "1; 2")]
    assert _pairs(arc.Studies[0].Comments) == [("s", "1; 2")]
    assert _pairs(arc.Assays[0].Comments) == [("x", "1; 2")]


def test_date_modified_stays_on_root_without_comment_node() -> None:
    arc_json = HarvestedArc.from_arctrl(_arc_with_duplicates()).arc_json
    graph = json.loads(arc_json)["@graph"]

    assert next(n for n in graph if n["@id"] == "./")["dateModified"] == "2024-09-04T09:34:30.938+0200"
    assert not [n for n in graph if n.get("name") == "dateModified"]
    assert "#LDComment_dateModified" not in arc_json


def test_crate_without_date_modified_is_unchanged() -> None:
    arc_json = ARC.from_arc_investigation(ArcInvestigation.create(identifier="i", title="T")).ToROCrateJsonString()

    assert drop_date_modified_comment_node(arc_json) == arc_json
