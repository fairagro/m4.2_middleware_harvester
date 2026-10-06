"""Unit tests for plugin-facing harvest error types."""

from middleware.contracts.errors import HarvesterError, RecordProcessingError, SkippedRecord


def test_skipped_record_is_not_an_exception() -> None:
    skip = SkippedRecord("duplicate", url="https://example.org/a")
    assert not isinstance(skip, Exception)
    assert not issubclass(SkippedRecord, HarvesterError)
    assert str(skip) == "duplicate"


def test_record_processing_error_carries_context() -> None:
    cause = ValueError("bad")
    err = RecordProcessingError("failed", record_id="rec-1", original_error=cause, url="https://example.org/a")
    assert isinstance(err, HarvesterError)
    assert err.record_id == "rec-1"
    assert err.original_error is cause
    assert err.url == "https://example.org/a"
    assert "record_id=rec-1" in str(err)
