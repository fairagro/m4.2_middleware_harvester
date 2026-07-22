"""Unit tests for source-URL annotations on api_client harvest errors."""

from types import SimpleNamespace

from middleware.api_client.models import HarvestErrorType
from middleware.harvester.main import _apply_client_errors, _format_source_url_annotation
from middleware.harvester.report import FailedRecord


def test_format_source_url_annotation_single_occurrence() -> None:
    assert _format_source_url_annotation({"https://example.org/a": 1}) == "source URL: https://example.org/a"


def test_format_source_url_annotation_repeated_same_url() -> None:
    assert _format_source_url_annotation({"https://example.org/a": 2}) == "source URL: https://example.org/a (×2)"


def test_format_source_url_annotation_multiple_urls_with_counts() -> None:
    annotation = _format_source_url_annotation(
        {
            "https://example.org/a": 2,
            "https://example.org/b": 1,
        }
    )
    assert annotation == "source URLs: https://example.org/a (×2), https://example.org/b"


def test_apply_client_errors_includes_occurrence_counts_for_duplicates() -> None:
    errors = [
        SimpleNamespace(
            error_type=HarvestErrorType.DUPLICATE,
            arc_id="arc-1",
            message="Duplicate ARC identifier 'arc-1' — two ARCs share the same identifier",
        )
    ]
    failed_records: list[FailedRecord] = []

    harvested, failed = _apply_client_errors(
        errors,
        {"arc-1": {"https://csw.example/record/1": 2}},
        harvested_datasets=2,
        failed_datasets=0,
        failed_records=failed_records,
    )

    assert harvested == 1
    assert failed == 1
    assert len(failed_records) == 1
    assert failed_records[0].record_id == "arc-1"
    assert "source URL: https://csw.example/record/1 (×2)" in failed_records[0].message
