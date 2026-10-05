"""Regression tests for value validation applied during ISO 19139 parsing.

These guard `openspec/specs/inspire-value-bounds/`. Behavioral: build a hostile/oversized
mock `MD_Metadata` and assert that `IsoParser.parse_record` rejects it with a
`ValidationError` (values are never truncated or dropped), or accepts well-formed input.
"""

# ruff: noqa: SLF001, PLR2004

from unittest.mock import MagicMock

import pytest
from owslib.iso import MD_DataIdentification, MD_Metadata  # type: ignore[import-untyped]
from pydantic import ValidationError

from middleware.inspire.iso_parser import IsoParser
from middleware.payload.inspire.models import InspireRecord
from middleware.payload.inspire.value_bounds import ValueBounds


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


DEFAULTS = ValueBounds()


@pytest.fixture
def parser() -> IsoParser:
    return IsoParser()


def _online(url: str) -> MagicMock:
    ol = MagicMock()
    ol.url = url
    ol.protocol = "WWW:DOWNLOAD"
    ol.protocol_url = None
    ol.name = "Data"
    ol.name_url = None
    ol.description = None
    ol.description_url = None
    ol.function = None
    return ol


def _with_online(record: MagicMock, *urls: str) -> None:
    dist = MagicMock()
    dist.format = None
    dist.online = [_online(u) for u in urls]
    record.distribution = dist


def test_well_formed_record_parses(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.language = "ger"
    mock_iso_record.charset = "utf8"
    mock_iso_record.hierarchy = "dataset"
    mock_iso_record.identification.topiccategory = ["farming"]

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.identifier == "uuid-123"
    assert rec.language == "ger"


@pytest.mark.parametrize(
    ("attr", "value", "field"),
    [
        ("title", "x" * (DEFAULTS.max_str_medium + 1), "title"),
        ("abstract", "x" * (DEFAULTS.max_str_long + 1), "abstract"),
        ("keywords", [f"kw{i}" for i in range(DEFAULTS.max_list_items + 1)], "keywords"),
    ],
)
def test_oversized_identification_value_is_rejected_not_truncated(
    mock_iso_record: MagicMock, parser: IsoParser, attr: str, value: object, field: str
) -> None:
    setattr(mock_iso_record.identification, attr, value)

    with pytest.raises(ValidationError, match=field):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_oversized_identifier_is_rejected_not_truncated(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    """Truncating would let two distinct fileIdentifiers collide on the same ARC."""
    mock_iso_record.identifier = "x" * (DEFAULTS.max_str_medium + 1)

    with pytest.raises(ValidationError, match="identifier"):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_error_message_does_not_echo_huge_value(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.abstract = "y" * 50_000

    with pytest.raises(ValidationError) as exc_info:
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert len(str(exc_info.value)) < 1_000


def test_configured_bounds_are_enforced(mock_iso_record: MagicMock) -> None:
    mock_iso_record.identification.keywords = ["a", "b", "c"]

    with pytest.raises(ValidationError, match="max_list_items=2"):
        IsoParser(ValueBounds(max_list_items=2)).parse_record(mock_iso_record, record_uuid="uuid-123")


def test_configured_bounds_reach_nested_models(mock_iso_record: MagicMock) -> None:
    """Context must propagate into OnlineResource, not only top-level InspireRecord fields."""
    _with_online(mock_iso_record, "https://example.com/data.csv")

    with pytest.raises(ValidationError, match="online_resources"):
        IsoParser(ValueBounds(allowed_url_schemes=frozenset({"ftp"}))).parse_record(
            mock_iso_record, record_uuid="uuid-123"
        )


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///etc/passwd", "data:text/html,x", "//evil/x"])
def test_graphic_overview_with_dangerous_scheme_is_rejected(
    mock_iso_record: MagicMock, parser: IsoParser, url: str
) -> None:
    mock_iso_record.identification.graphicoverview = ["http://ok.example/thumb.png", url]

    with pytest.raises(ValidationError, match="graphic_overviews"):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_online_resource_with_bad_scheme_url_is_rejected(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    _with_online(mock_iso_record, "javascript:alert(1)", "https://example.com/data.csv")

    with pytest.raises(ValidationError, match="online_resources"):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_ftp_online_resource_is_accepted_by_default(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    """INSPIRE download links are commonly ftp://; the default scheme policy keeps them."""
    _with_online(mock_iso_record, "ftp://ftp.example.com/data.zip")

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.online_resources[0].url == "ftp://ftp.example.com/data.zip"


def test_resource_identifier_url_code_is_validated(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.uricode = ["https://doi.org/10.1234/x", "10.1234/plain-doi"]
    mock_iso_record.identification.uricodespace = ["DOI", "DOI"]

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.resource_identifiers[0].url == "https://doi.org/10.1234/x"
    assert rec.resource_identifiers[1].url is None


def test_malformed_denominator_is_rejected(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.denominators = ["5000", "not-a-number"]

    with pytest.raises(ValidationError, match="spatial_resolution_denominators"):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_numeric_string_denominators_are_converted(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.denominators = ["5000", "3000"]

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.spatial_resolution_denominators == [5000, 3000]


def test_malformed_distance_is_rejected(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.distance = ["10", "ten"]
    mock_iso_record.identification.uom = ["m", "m"]

    with pytest.raises(ValidationError, match="spatial_resolution_distances"):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_numeric_string_distances_are_converted(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.identification.distance = ["10", "2.5"]
    mock_iso_record.identification.uom = ["m"]

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert [(d.value, d.uom) for d in rec.spatial_resolution_distances] == [(10.0, "m"), (2.5, "m")]


def test_datestamp_with_oversized_fraction_is_rejected(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.datestamp = "2020-01-01T00:00:00." + "1" * 10_000

    with pytest.raises(ValidationError, match="date_stamp"):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_datestamp_with_nanosecond_fraction_is_kept(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.datestamp = "2020-01-01T00:00:00.123456789Z"

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.date_stamp == "2020-01-01T00:00:00.123456789Z"


@pytest.mark.parametrize("extent", [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0, 4.0, 5.0]])
def test_spatial_extent_must_be_a_four_value_bbox(
    mock_iso_record: MagicMock, parser: IsoParser, extent: list[float]
) -> None:
    data = parser.parse_record(mock_iso_record, record_uuid="uuid-123").model_dump()

    with pytest.raises(ValidationError, match="spatial_extent"):
        InspireRecord.model_validate({**data, "spatial_extent": extent})


def test_dataset_uri_with_dangerous_scheme_is_rejected(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.dataseturi = "javascript:alert(1)"

    with pytest.raises(ValidationError, match="dataset_uri"):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_dataset_uri_with_http_scheme_is_kept(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    mock_iso_record.dataseturi = "https://example.com/dataset/1"

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.dataset_uri == "https://example.com/dataset/1"


@pytest.mark.parametrize(
    ("attr", "value", "field"),
    [
        ("language", "de", "language"),  # ISO 639-1, INSPIRE mandates ISO 639-2
        ("language", "German", "language"),
        ("charset", "utf-8", "charset"),  # MD_CharacterSetCode is "utf8"
        ("hierarchy", "folder", "hierarchy"),
        ("datestamp", "yesterday", "date_stamp"),
    ],
)
def test_metadata_codelist_violation_is_rejected(
    mock_iso_record: MagicMock, parser: IsoParser, attr: str, value: str, field: str
) -> None:
    setattr(mock_iso_record, attr, value)

    with pytest.raises(ValidationError, match=field):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


@pytest.mark.parametrize(
    ("attr", "value", "field"),
    [
        ("status", "done", "status"),
        ("topiccategory", ["agriculture"], "topic_categories"),
        ("resourcelanguagecode", ["en"], "resource_language"),
    ],
)
def test_identification_codelist_violation_is_rejected(
    mock_iso_record: MagicMock, parser: IsoParser, attr: str, value: object, field: str
) -> None:
    setattr(mock_iso_record.identification, attr, value)

    with pytest.raises(ValidationError, match=field):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_citation_date_type_and_format_are_validated(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    good = MagicMock(date="2023-05-01T10:00:00Z", type="publication")
    bad = MagicMock(date="2023-05-01", type="published")
    mock_iso_record.identification.date = [good, bad]

    with pytest.raises(ValidationError, match=r"dates\.1\.datetype"):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_contact_role_and_email_are_validated(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    contact = MagicMock()
    contact.name = "Jane Doe"
    contact.organization = "Org"
    contact.email = "not an email"
    contact.role = "boss"
    mock_iso_record.contact = [contact]

    with pytest.raises(ValidationError) as exc_info:
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    locs = {err["loc"] for err in exc_info.value.errors()}
    assert ("contacts", 0, "email") in locs
    assert ("contacts", 0, "role") in locs


def test_dataset_uri_accepts_urn(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    """gmd:dataSetURI is a URI: a URN (seen on GDI-DE) is legitimate, not a bad URL."""
    mock_iso_record.dataseturi = "urn:sde:WAGIS1::sde:sde.GISADMIN.NSW_Einleitung_Pkt"

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.dataset_uri == "urn:sde:WAGIS1::sde:sde.GISADMIN.NSW_Einleitung_Pkt"


@pytest.mark.parametrize("junk", ["I", "?ResourceName=", "G:\\data\\x.shp"])
def test_dataset_uri_rejects_non_uri_junk(mock_iso_record: MagicMock, parser: IsoParser, junk: str) -> None:
    """Values observed on GDI-DE that are neither URL nor URN."""
    mock_iso_record.dataseturi = junk

    with pytest.raises(ValidationError, match="dataset_uri"):
        parser.parse_record(mock_iso_record, record_uuid="uuid-123")


def test_blank_optional_url_means_absent(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    """OWSLib reports an absent gmx:Anchor href as "" — that must not reject the record."""
    _with_online(mock_iso_record, "https://example.com/data.csv")
    mock_iso_record.distribution.online[0].name_url = ""
    mock_iso_record.distribution.online[0].protocol_url = "  "

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.online_resources[0].name_url is None
    assert rec.online_resources[0].protocol_url is None


def test_placeholders_in_optional_fields_mean_absent(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    """BonaRes writes gco:CharacterString "None" / "No information provided" for empty elements (#413)."""
    ident = mock_iso_record.identification
    ident.purpose = "None"
    ident.supplementalinformation = " No information provided "
    ident.otherconstraints = ["None", "Not Specified: The original author did not specify a license."]
    ident.graphicoverview = ["None", "https://example.com/thumb.png"]
    _with_online(mock_iso_record, "https://example.com/data.csv")
    mock_iso_record.distribution.online[0].description = "N/A"

    rec = parser.parse_record(mock_iso_record, record_uuid="uuid-123")

    assert rec.purpose is None
    assert rec.supplemental_information is None
    assert rec.other_constraints == ["Not Specified: The original author did not specify a license."]
    assert rec.graphic_overviews == ["https://example.com/thumb.png"]
    assert rec.online_resources[0].description is None


def test_placeholder_in_required_field_is_kept(mock_iso_record: MagicMock, parser: IsoParser) -> None:
    """Required title/abstract keep the source value; dropping them would fail the whole record."""
    mock_iso_record.identification.abstract = "No abstract provided"

    assert parser.parse_record(mock_iso_record, record_uuid="uuid-123").abstract == "No abstract provided"


def test_configured_placeholder_values_replace_defaults(mock_iso_record: MagicMock) -> None:
    mock_iso_record.identification.purpose = "Keine Angabe"
    mock_iso_record.identification.edition = "None"

    rec = IsoParser(placeholder_values=frozenset({"keine angabe"})).parse_record(
        mock_iso_record, record_uuid="uuid-123"
    )

    assert rec.purpose is None
    assert rec.edition == "None"
