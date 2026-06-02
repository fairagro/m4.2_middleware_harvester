"""JSON-LD harvest report generation and stdout printing."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

_JSON_LD_CONTEXT = {
    "@vocab": "https://schema.org/",
    "schema": "https://schema.org/",
    "fairagro": "https://fairagro.net/ns/",
}


def _format_iso_duration(seconds: float) -> str:
    """Serialize a duration value as an ISO 8601 duration string."""
    remainder = f"{seconds:.6f}".rstrip("0").rstrip(".")
    if remainder == "":
        remainder = "0"
    return f"PT{remainder}S"


def _format_iso_timestamp(value: datetime) -> str:
    """Format a UTC datetime value as an ISO 8601 timestamp ending in Z."""
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class FailedRecord:
    """A single dataset that failed during harvesting, with its error message and optional identifier."""

    message: str
    record_id: str | None = None
    url: str | None = None


@dataclass
class HarvestUploadResult:
    """Aggregated result of a single plugin's harvest-and-upload cycle."""

    harvest_id: str | None
    harvested_datasets: int | None
    failed_datasets: int | None
    skipped_datasets: int
    harvest_started: bool
    failed_records: list[FailedRecord]


@dataclass(frozen=True)
class RepositoryReport:
    """Execution statistics for a single harvested repository."""

    rdi: str
    harvest_id: str | None
    duration_seconds: float
    expected_datasets: int | None
    harvested_datasets: int | None
    failed_datasets: int | None
    skipped_datasets: int = 0
    failed_records: tuple[FailedRecord, ...] = ()

    def to_jsonld(self) -> dict[str, Any]:
        """Convert the repository report to a JSON-LD dictionary."""
        result: dict[str, Any] = {
            "@type": "schema:EntryPoint",
            "name": self.rdi,
            "identifier": self.rdi,
            "schema:duration": _format_iso_duration(self.duration_seconds),
        }
        if self.harvested_datasets is not None:
            result["fairagro:harvestedDatasets"] = self.harvested_datasets
        result["fairagro:harvestId"] = self.harvest_id
        if self.expected_datasets is not None:
            result["fairagro:expectedDatasets"] = self.expected_datasets
        result["fairagro:skippedDatasets"] = self.skipped_datasets
        if self.failed_datasets is not None:
            result["fairagro:failedDatasets"] = self.failed_datasets
        if self.failed_records:
            result["fairagro:failedRecords"] = [
                {
                    "fairagro:message": r.message,
                    **({"fairagro:recordId": r.record_id} if r.record_id else {}),
                    **({"fairagro:url": r.url} if r.url else {}),
                }
                for r in self.failed_records
            ]
        return result


@dataclass(frozen=True)
class HarvestReport:
    """Summary statistics for an entire harvest run."""

    start_time: datetime
    end_time: datetime
    repository_reports: list[RepositoryReport]

    @property
    def duration_seconds(self) -> float:
        """Return the total harvest run duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def all_failed(self) -> bool:
        """Return True when every repository harvest failed to produce a harvest ID."""
        return bool(self.repository_reports) and all(report.harvest_id is None for report in self.repository_reports)

    def to_jsonld(self) -> dict[str, Any]:
        """Convert the full harvest report into a JSON-LD object."""
        return {
            "@context": _JSON_LD_CONTEXT,
            "@type": "schema:Action",
            "name": "FAIRagro Harvest Run",
            "schema:startTime": _format_iso_timestamp(self.start_time),
            "schema:endTime": _format_iso_timestamp(self.end_time),
            "fairagro:harvestDurationSeconds": self.duration_seconds,
            "schema:result": [report.to_jsonld() for report in self.repository_reports],
        }


def print_report(report: HarvestReport) -> None:
    """Serialize the report to JSON-LD and print it to stdout."""
    try:
        json_text = json.dumps(report.to_jsonld(), ensure_ascii=False, indent=2)
        print(json_text)
    except (OSError, OverflowError, TypeError, ValueError) as exc:
        logger.warning("Failed to serialise harvest report: %s", exc)
