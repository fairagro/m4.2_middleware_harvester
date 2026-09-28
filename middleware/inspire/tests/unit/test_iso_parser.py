"""Regression tests for defensive bounds applied during ISO 19139 parsing.

These guard `openspec/specs/inspire-value-bounds/`. Behavioral: build a hostile/oversized
mock `MD_Metadata` and assert what `IsoParser.parse_record` returns, not which helper it
called internally.
"""

# ruff: noqa: SLF001, PLR2004

from unittest.mock import MagicMock

import pytest
from owslib.iso import MD_DataIdentification, MD_Metadata  # type: ignore[import-untyped]

from middleware.inspire.iso_parser import IsoParser
from middleware.inspire.value_bounds import MAX_LIST_ITEMS, MAX_STR_LONG, MAX_STR_MEDIUM


@pytest.fixture
def create_mock_identification() -> MagicMock:
    """Minimal identification mock — same shape as test_harvester_comprehensive.py's."""
    identification = MagicMock(spec=MD_DataIdentification)
    identification.title = "Test Title"
    identification.abstract = "Test Abstract"
    identification.keywords = []
    identification.topiccategory = []
    identification.contact = []
    identification.bbox = None
    identification.temporalextent_start = None
    identification.resourceconstraint = []
    identification.uricode = []
    identification.uricodespace = []
    identification.date = []
    identification.resourcelanguagecode = []
    identification.resourcelanguage = []
    identification.graphicoverview = []
    identification.denominators = []
    identification.distance = []
    identification.uom = []
    identification.creator = []
    identification.publisher = []
    identification.contributor = []
    identification.accessconstraints = []
    identification.useconstraints = []
    identification.classification = []
    identification.otherconstraints = []
    identification.otherconstraints_url = []
    identification.edition = None
    identification.purpose = None
    identification.status = None
    identification.supplementalinformation = None
    identification.alternatetitle = None
    return identification


@pytest.fixture
def mock_iso_record(create_mock_identification: MagicMock) -> MagicMock:
    record = MagicMock(spec=MD_Metadata)
    record.identifier = "uuid-123"
    record.datestamp = "2023-01-01"
    record.identification = create_mock_identification
    record.contact = []
    record.dataquality = None
    record.distribution = None
    record.referencesystem = None
    record.parentidentifier = None
    record.language = None
    record.languagecode = None
    record.charset = None
    record.hierarchy = None
    record.stdname = None
    record.stdver = None
    record.dataseturi = None
    return record


@pytest.fixture
def parser() -> IsoParser:
    return IsoParser()


def test_oversized_title_is_truncated_not_rejected(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.title = "x" * (MAX_STR_MEDIUM + 500)

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert len(rec.title) == MAX_STR_MEDIUM


def test_oversized_abstract_is_truncated_not_rejected(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.abstract = "x" * (MAX_STR_LONG + 5_000)

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert len(rec.abstract) == MAX_STR_LONG


def test_oversized_keyword_list_is_capped(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.keywords = [f"kw{i}" for i in range(MAX_LIST_ITEMS + 100)]

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert len(rec.keywords) == MAX_LIST_ITEMS


def test_graphic_overview_with_dangerous_scheme_is_dropped_good_one_kept(
    mock_iso_record: MagicMock, parser: IsoParser
) -> None:
    mock_iso_record.identification.graphicoverview = [
        "javascript:alert(1)",
        "http://ok.example/thumb.png",
        "file:///etc/passwd",
    ]

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.graphic_overviews == ["http://ok.example/thumb.png"]


def test_online_resource_with_bad_scheme_url_is_dropped_entirely(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    dist = MagicMock()
    dist.format = None
    bad = MagicMock()
    bad.url = "javascript:alert(1)"
    good = MagicMock()
    good.url = "https://example.com/data.csv"
    good.protocol = "WWW:DOWNLOAD"
    good.protocol_url = None
    good.name = "Data"
    good.name_url = None
    good.description = None
    good.description_url = None
    good.function = None
    dist.online = [bad, good]
    mock_iso_record.distribution = dist

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert len(rec.online_resources) == 1
    assert rec.online_resources[0].url == "https://example.com/data.csv"


def test_resource_identifier_url_rejects_non_http_scheme(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.uricode = ["ftp://example.com/doi"]
    mock_iso_record.identification.uricodespace = ["DOI"]

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert len(rec.resource_identifiers) == 1
    assert rec.resource_identifiers[0].code == "ftp://example.com/doi"
    assert rec.resource_identifiers[0].url is None


def test_malformed_denominator_is_dropped_record_still_parses(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    """Key regression.

    Today this raises ValueError uncaught -> RecordProcessingError for the whole record.
    After bounding, one bad denominator is dropped, not fatal.
    """
    mock_iso_record.identification.denominators = ["5000", "not-a-number", "3000"]

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.spatial_resolution_denominators == [5000, 3000]


def test_dataset_uri_with_dangerous_scheme_is_dropped(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.dataseturi = "javascript:alert(1)"

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.dataset_uri is None


def test_dataset_uri_with_http_scheme_is_kept(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.dataseturi = "https://example.com/dataset/1"

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.dataset_uri == "https://example.com/dataset/1"
