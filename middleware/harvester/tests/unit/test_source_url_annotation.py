"""Unit tests for source-URL annotations on api_client harvest errors."""

from types import SimpleNamespace

from middleware.api_client.models import HarvestErrorType
from middleware.harvester.reporting import (
    ArcStreamState,
    format_source_url_annotation,
    record_upload_outcomes,
)
from middleware.shared.report import HarvestReport


def test_format_source_url_annotation_single_occurrence() -> None:
    assert format_source_url_annotation({"https://example.org/a": 1}) == "source URL: https://example.org/a"


def test_format_source_url_annotation_repeated_same_url() -> None:
    assert format_source_url_annotation({"https://example.org/a": 2}) == "source URL: https://example.org/a (×2)"


def test_format_source_url_annotation_multiple_urls_with_counts() -> None:
    annotation = format_source_url_annotation(
        {
            "https://example.org/a": 2,
            "https://example.org/b": 1,
        }
    )
    assert annotation == "source URLs: https://example.org/a (×2), https://example.org/b"


def test_record_upload_outcomes_counts_from_api_result() -> None:
    """Harvested = submitted - errors; each API error becomes record_failed."""
    errors = [
        SimpleNamespace(
            error_type=HarvestErrorType.DUPLICATE,
            arc_id="arc-1",
            message="Duplicate ARC identifier 'arc-1' — two ARCs share the same identifier",
        )
    ]
    state = ArcStreamState(
        arc_id_to_url_counts={"arc-1": {"https://csw.example/record/1": 2}},
        submitted=2,
        studies=2,
        assays=1,
    )
    report = HarvestReport()
    scope = report.open_repository("bonares")

    record_upload_outcomes(errors, state, scope)

    snap = scope.snapshot()
    assert snap.harvested_datasets == 1
    assert snap.failed_datasets == 1
    assert snap.total_studies == 2
    assert snap.total_assays == 1
    assert len(snap.failed_records) == 1
    assert snap.failed_records[0].record_id == "arc-1"
    assert "source URL: https://csw.example/record/1 (×2)" in snap.failed_records[0].message
