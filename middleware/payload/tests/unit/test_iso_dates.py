"""ISO 8601 date normalisation (#409) and its use in the Schema.org mapper."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from arctrl import ARC  # type: ignore[import-untyped]
from mapper_test_helpers import NO_DISCOVERY, first_harvest, parse_jsonld, root_dates

from middleware.payload.iso_dates import iso_date
from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # ISO shapes seen in the DataHUB export pass through unchanged.
        ("2011", "2011"),
        ("2011-01", "2011-01"),
        ("2011-01-01", "2011-01-01"),
        (" 2024-05-02T10:11:12.123456 ", "2024-05-02T10:11:12.123456"),
        ("2024-05-02T10:11:12Z", "2024-05-02T10:11:12Z"),
        ("2024-05-02T10:11:12+02:00", "2024-05-02T10:11:12+02:00"),
        # e!DAL Java Date.toString(): local day and time kept, offset from the zone.
        ("Sat Jan 01 00:00:00 CET 2011", "2011-01-01T00:00:00+01:00"),
        ("Tue Jul 15 13:52:48 CEST 2014", "2014-07-15T13:52:48+02:00"),
        ("Mon Mar 3 09:17:44 UTC 2025", "2025-03-03T09:17:44+00:00"),
        # Not dates.
        ("Sat Jan 01 00:00:00 IST 2011", None),
        ("Sat Feb 30 00:00:00 CET 2011", None),
        ("Sat Foo 01 00:00:00 CET 2011", None),
        ("01.01.2011", None),
        ("unknown", None),
        ("", None),
        (None, None),
    ],
)
def test_iso_date(value: str | None, expected: str | None) -> None:
    assert iso_date(value) == expected


def _arc_json(**dates: str) -> str:
    payload = json.dumps({
        "@context": {"@vocab": "https://schema.org/"},
        "@id": "https://doi.org/10.5447/ipk/2011/0",
        "@type": "Dataset",
        "name": "e!DAL dataset",
        **dates,
    })
    return first_harvest(GeneralSchemaOrgMapper().map_graph(parse_jsonld(payload), NO_DISCOVERY)).arc_json


def _map(**dates: str) -> ARC:
    return ARC.from_rocrate_json_string(_arc_json(**dates))


def _comments(arc: ARC) -> list[tuple[str, str]]:
    return [(c.Name, c.Value) for c in arc.Comments if c.Name.startswith("Unparsed")]


def test_edal_java_date_becomes_iso_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        arc = _map(datePublished="Sat Jan 01 00:00:00 CET 2011")

    assert arc.PublicReleaseDate == "2011-01-01T00:00:00+01:00"
    assert arc.Studies[0].PublicReleaseDate == "2011-01-01T00:00:00+01:00"
    assert not _comments(arc)
    assert ["normalised to 2011-01-01T00:00:00+01:00" in r.getMessage() for r in caplog.records] == [True]


def test_iso_date_kept_without_warning(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        arc = _map(datePublished="2011")
    assert arc.PublicReleaseDate == "2011"
    assert not caplog.records


def test_unparseable_date_is_comment_not_date(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        arc = _map(datePublished="sometime in 2011")

    # No date at all: ARCtrl stamps the serialisation time, as before.
    assert not arc.SubmissionDate
    assert not arc.Studies[0].PublicReleaseDate
    assert _comments(arc) == [("Unparsed datePublished", "sometime in 2011")]
    assert len(caplog.records) == 1


def test_unparseable_date_published_falls_back_to_date_modified() -> None:
    arc = _map(datePublished="n/a", dateModified="Tue Jul 15 13:52:48 CEST 2014")
    assert arc.PublicReleaseDate == "2014-07-15T13:52:48+02:00"
    assert _comments(arc) == [("Unparsed datePublished", "n/a")]


# --- dateCreated / datePublished (#407) -------------------------------------


def test_date_published_is_release_date_and_date_created_is_submission_date() -> None:
    """e!DAL 10.5447/ipk/2011/0: the publication date must not end up as RO-Crate dateCreated."""
    arc = _map(datePublished="Sat Jan 01 00:00:00 CET 2011", dateCreated="2010-06-30")

    assert (arc.PublicReleaseDate, arc.SubmissionDate) == ("2011-01-01T00:00:00+01:00", "2010-06-30")
    study = arc.Studies[0]
    assert (study.PublicReleaseDate, study.SubmissionDate) == ("2011-01-01T00:00:00+01:00", "2010-06-30")


def test_date_published_only_leaves_date_created_out() -> None:
    """No ``dateCreated: ""`` on the RO-Crate root (e!DAL has no creation date)."""
    assert root_dates(_arc_json(datePublished="2011-01-01")) == {"datePublished": "2011-01-01"}


def test_no_source_date_is_not_an_empty_date() -> None:
    """Without any source date ARCtrl stamps the serialisation time; the mapper must not write ``""``."""
    dates = root_dates(_arc_json())
    assert list(dates) == ["datePublished"]
    assert dates["datePublished"]


@pytest.mark.parametrize(
    ("dates", "expected"),
    [
        ({"datePublished": "2011", "dateModified": "2014", "dateCreated": "2010"}, "2011"),
        ({"dateModified": "2014", "dateCreated": "2010"}, "2014"),
        ({"dateCreated": "2010"}, "2010"),
    ],
)
def test_release_date_falls_back_to_modified_then_created(dates: dict[str, str], expected: str) -> None:
    """Any source date beats the harvest time ARCtrl would stamp as datePublished."""
    assert _map(**dates).PublicReleaseDate == expected


def test_date_published_survives_the_api_round_trip(tmp_path: Path) -> None:
    """The API reads the RO-Crate and writes it with ARC.Write; the export must keep the source date."""
    arc = _map(datePublished="2011-01-01", dateCreated="2010-06-30")
    arc.Write(str(tmp_path))

    stored = ARC.load(str(tmp_path))
    crate_root = next(n for n in json.loads(stored.ToROCrateJsonString())["@graph"] if n["@id"] == "./")
    assert (crate_root["datePublished"], crate_root["dateCreated"]) == ("2011-01-01", "2010-06-30")
