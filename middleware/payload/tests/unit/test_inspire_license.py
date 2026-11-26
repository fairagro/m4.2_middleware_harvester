"""Unit tests for INSPIRE ``gmd:otherConstraints`` → ``ARC.License`` (#485)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from arctrl import ARC  # type: ignore[import-untyped]

from middleware.payload.inspire.license import (
    inspire_license,
    is_inspire_licence_constraint,
    is_inspire_licence_url,
)
from middleware.payload.inspire.mapper import InspireMapper
from middleware.payload.inspire.models import InspireRecord

CC_BY = "https://creativecommons.org/licenses/by/4.0/"
ARCTRL_DEFAULT = "ALL RIGHTS RESERVED BY THE AUTHORS"

BONARES_CC_BY = (
    "CC-BY (CC-BY): https://creativecommons.org/licenses/by/4.0/ "
    "(https://creativecommons.org/licenses/by/4.0/legalcode)"
)
THUENEN_DL_DE = (
    "Data licence Germany – attribution – version 2.0 (dl-de/by-2-0): Data licence Germany – attribution – "
    "version 2.0. See info at: https://www.govdata.de/dl-de/by-2-0 (http://www.govdata.de/dl-de/by-2-0)"
)
NOT_SPECIFIED = "Not Specified: The original author did not specify a license."

DWD_JSON_CC_BY = (
    '{"id": "cc-by/4.0","name": "Creative Commons Namensnennung – 4.0 International (CC BY 4.0)",'
    '"url": "https://creativecommons.org/licenses/by/4.0/",'
    '"quelle": "Datenquelle: CC-BY-4.0 - [Deutscher Wetterdienst](https://www.dwd.de/copyright)"}'
)


def _license_text(arc_json: str) -> str | None:
    """Text of the RO-Crate licence node the root dataset points to."""
    graph = json.loads(arc_json)["@graph"]
    root = next(node for node in graph if node.get("@id") == "./")
    license_id = root["license"]["@id"]
    node = next(node for node in graph if node.get("@id") == license_id)
    text = node.get("text")
    return str(text) if text is not None else None


def _inspire_record(other_constraints: list[str]) -> InspireRecord:
    return InspireRecord.model_validate({
        "identifier": "uuid-licence",
        "title": "INSPIRE licence",
        "abstract": "Abstract",
        "other_constraints": other_constraints,
    })


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (CC_BY, True),
        ("https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply", False),
        ("not-a-url", False),
        ("", False),
    ],
)
def test_is_inspire_licence_url(url: str, expected: bool) -> None:
    assert is_inspire_licence_url(url) is expected


@pytest.mark.parametrize(
    ("constraint", "expected"),
    [
        (BONARES_CC_BY, True),
        (
            '{"id": "cc-by/4.0", "name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"}',
            True,
        ),
        ("See https://creativecommons.org/licenses/by/4.0/", True),
        (NOT_SPECIFIED, False),
        ("available on request from the data owner", False),
        ("keine", False),
    ],
)
def test_is_inspire_licence_constraint(constraint: str, expected: bool) -> None:
    assert is_inspire_licence_constraint(constraint) is expected


@pytest.mark.parametrize(
    "constraints",
    [
        [BONARES_CC_BY, "Disclaimer Author (en) These data were created …"],
        [THUENEN_DL_DE],
        ["None", "GeoNutzV (GeoNutzV): Verordnung … (http://www.gesetze-im-internet.de/geonutzv/)"],
    ],
)
def test_inspire_license_takes_first_geonode_licence_text(constraints: list[str]) -> None:
    license_ = inspire_license(constraints, [])
    expected = next(c for c in constraints if " (" in c and "):" in c)
    assert license_ is not None
    assert license_.Content == expected
    assert license_.Path == "LICENSE"


def test_inspire_license_prefers_non_registry_anchor_url() -> None:
    license_ = inspire_license(
        ["Datenlizenz Deutschland – Namensnennung – Version 2.0"],
        [
            "http://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply",
            "https://www.govdata.de/dl-de/by-2-0",
        ],
    )
    assert license_ is not None
    assert license_.Content == "https://www.govdata.de/dl-de/by-2-0"


def test_inspire_license_gdi_de_json_wins_over_bare_licence_url() -> None:
    """DWD often ships both GDI-DE JSON and a CC URL; keep name (url), not the bare URL (#485)."""
    license_ = inspire_license(
        [DWD_JSON_CC_BY],
        [CC_BY],
    )
    assert license_ is not None
    assert license_.Content == (
        "Creative Commons Namensnennung – 4.0 International (CC BY 4.0) (https://creativecommons.org/licenses/by/4.0/)"
    )


def test_inspire_license_gdi_de_json_uses_name_and_url() -> None:
    """DWD via GDI-DE: the JSON licence wins over free text that also names the licence (#485)."""
    license_ = inspire_license(
        [
            (
                'Nutzungsbedingungen: Es gelten die Bedingungen der Lizenz Creative Commons BY 4.0 "CC BY 4.0". '
                'Einzelheiten unter "https://www.dwd.de/copyright".'
            ),
            DWD_JSON_CC_BY,
            "Es gelten keine Zugriffsbeschränkungen",
        ],
        ["http://inspire.ec.europa.eu/metadata-codelist/LimitationsOnPublicAccess/noLimitations"],
    )
    assert license_ is not None
    assert license_.Content == (
        "Creative Commons Namensnennung – 4.0 International (CC BY 4.0) (https://creativecommons.org/licenses/by/4.0/)"
    )


def test_inspire_license_gdi_de_json_without_name_uses_url() -> None:
    license_ = inspire_license(['{"id": "cc-by/4.0", "url": "https://creativecommons.org/licenses/by/4.0/"}'], [])
    assert license_ is not None
    assert license_.Content == "https://creativecommons.org/licenses/by/4.0/"


def test_inspire_license_gdi_de_malformed_json_still_reads_name_and_url() -> None:
    """Live DWD record with a stray backslash after ``name`` (invalid JSON)."""
    license_ = inspire_license(
        ['{"id": "cc-by/4.0","name\\": "CC BY 4.0","url": "https://creativecommons.org/licenses/by/4.0/"}'], []
    )
    assert license_ is not None
    assert license_.Content == "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)"


@pytest.mark.parametrize(
    "constraint",
    ['{"id": "cc-by/4.0", "name": "CC BY 4.0"}', '{"url": "not a url"}', "{broken", '{"url": ["x"]}'],
)
def test_inspire_license_gdi_de_json_without_http_url_is_no_licence(constraint: str) -> None:
    assert inspire_license([constraint], []) is None


def test_inspire_license_free_text_with_licence_host_url() -> None:
    text = "Nutzung gemäß https://creativecommons.org/licenses/by/4.0/ mit Quellenangabe"
    license_ = inspire_license(["keine", text], [])
    assert license_ is not None
    assert license_.Content == text


@pytest.mark.parametrize(
    "constraints",
    [
        [],
        [NOT_SPECIFIED],
        [f"{NOT_SPECIFIED}", "None"],
        [NOT_SPECIFIED, "see https://creativecommons.org/licenses/by/4.0/"],
        ["Access for data download upon request to someone@example.org."],
        ["Data are available on request.", "keine", "See info at https://www.example.org/terms"],
    ],
)
def test_inspire_license_none_without_licence(constraints: list[str]) -> None:
    assert inspire_license(constraints, ["", ""]) is None


@pytest.mark.parametrize(
    ("constraints", "expected"),
    [([BONARES_CC_BY], BONARES_CC_BY), ([NOT_SPECIFIED], ARCTRL_DEFAULT)],
)
def test_inspire_mapper_sets_licence(constraints: list[str], expected: str) -> None:
    arc = InspireMapper().map_record(_inspire_record(constraints))
    assert _license_text(arc.ToROCrateJsonString()) == expected


def test_inspire_mapper_omits_licence_bearing_other_constraints_comments() -> None:
    """Licence JSON/GeoNode text feed ARC.License only; access notes may stay as Comments (#485)."""
    gdi = (
        '{"id": "cc-by/4.0", "name": "Creative Commons Namensnennung – 4.0 International (CC BY 4.0)", '
        '"url": "https://creativecommons.org/licenses/by/4.0/"}'
    )
    access_note = "available on request from the data owner"
    record = InspireRecord.model_validate({
        "identifier": "uuid-licence-dual",
        "title": "DWD-shaped licence",
        "abstract": "Abstract",
        "other_constraints": [gdi, access_note],
        "other_constraints_url": [CC_BY, "https://inspire.ec.europa.eu/metadata-codelist/x"],
    })
    arc_json = InspireMapper().map_record(record).ToROCrateJsonString()
    assert _license_text(arc_json) == (
        "Creative Commons Namensnennung – 4.0 International (CC BY 4.0) (https://creativecommons.org/licenses/by/4.0/)"
    )
    assert '"name": "Other Constraints"' in arc_json or "Other Constraints" in arc_json
    assert access_note in arc_json
    assert gdi not in arc_json
    assert CC_BY not in [
        c.get("text")
        for c in json.loads(arc_json)["@graph"]
        if c.get("name") in {"Other Constraints", "Other Constraints URLs"}
    ]
    url_comments = [
        c.get("text", "") for c in json.loads(arc_json)["@graph"] if c.get("name") == "Other Constraints URLs"
    ]
    assert all(CC_BY not in str(text) for text in url_comments)
    assert 'Comment {Name = "License"' not in arc_json


def test_inspire_mapper_gdi_json_only_sets_licence_without_other_constraints_comment() -> None:
    gdi = (
        '{"id": "cc-by/4.0", "name": "Creative Commons Namensnennung – 4.0 International (CC BY 4.0)", '
        '"url": "https://creativecommons.org/licenses/by/4.0/"}'
    )
    arc_json = InspireMapper().map_record(_inspire_record([gdi])).ToROCrateJsonString()
    expected = (
        "Creative Commons Namensnennung – 4.0 International (CC BY 4.0) (https://creativecommons.org/licenses/by/4.0/)"
    )
    assert _license_text(arc_json) == expected
    assert "Other Constraints" not in [
        c.get("name") for c in json.loads(arc_json)["@graph"] if isinstance(c.get("name"), str)
    ]
    assert gdi not in arc_json


def test_licence_round_trips_through_arc_write_without_url_paths(tmp_path: Path) -> None:
    """The API rebuilds ARCs from these RO-Crates and writes them; the licence must stay a file."""
    arc_json = InspireMapper().map_record(_inspire_record([BONARES_CC_BY])).ToROCrateJsonString()
    arc = ARC.from_rocrate_json_string(arc_json)
    assert arc.License.Content == BONARES_CC_BY

    arc.Write(str(tmp_path))

    assert (tmp_path / "LICENSE").read_text(encoding="utf-8") == BONARES_CC_BY
    for _root, dirnames, _files in os.walk(tmp_path):
        assert not [d for d in dirnames if d.startswith("http")]
