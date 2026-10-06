"""ISO 8601 date normalisation (#409) and its use in the Schema.org mapper."""

from __future__ import annotations

import json
import logging

import pytest
from arctrl import ARC  # type: ignore[import-untyped]
from mapper_test_helpers import NO_DISCOVERY, first_harvest, parse_jsonld

from middleware.payload.iso_dates import iso_date
from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.placeholders import PlaceholderConfig


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


def _map(**dates: str) -> ARC:
    payload = json.dumps({
        "@context": {"@vocab": "https://schema.org/"},
        "@id": "https://doi.org/10.5447/ipk/2011/0",
        "@type": "Dataset",
        "name": "e!DAL dataset",
        **dates,
    })
    arc_json = first_harvest(
        GeneralSchemaOrgMapper(PlaceholderConfig()).map_graph(parse_jsonld(payload), NO_DISCOVERY)
    ).arc_json
    return ARC.from_rocrate_json_string(arc_json)


def _comments(arc: ARC) -> list[tuple[str, str]]:
    return [(c.Name, c.Value) for c in arc.Comments if c.Name.startswith("Unparsed")]


def test_edal_java_date_becomes_iso_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        arc = _map(datePublished="Sat Jan 01 00:00:00 CET 2011")

    assert arc.SubmissionDate == "2011-01-01T00:00:00+01:00"
    assert arc.Studies[0].SubmissionDate == "2011-01-01T00:00:00+01:00"
    assert not _comments(arc)
    assert ["normalised to 2011-01-01T00:00:00+01:00" in r.getMessage() for r in caplog.records] == [True]


def test_iso_date_kept_without_warning(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        arc = _map(datePublished="2011")
    assert arc.SubmissionDate == "2011"
    assert not caplog.records


def test_unparseable_date_is_comment_not_date(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        arc = _map(datePublished="sometime in 2011")

    assert not arc.SubmissionDate
    assert not arc.Studies[0].SubmissionDate
    assert _comments(arc) == [("Unparsed datePublished", "sometime in 2011")]
    assert len(caplog.records) == 1


def test_unparseable_date_published_falls_back_to_date_modified() -> None:
    arc = _map(datePublished="n/a", dateModified="Tue Jul 15 13:52:48 CEST 2014")
    assert arc.SubmissionDate == "2014-07-15T13:52:48+02:00"
    assert _comments(arc) == [("Unparsed datePublished", "n/a")]
