"""Harvest-report wiring: scope updates and stdout emission."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from middleware.harvester.errors import HarvesterError, RecordProcessingError, SkippedRecord
from middleware.shared.report import HarvestReport, JsonLdReportSerializer, RepositoryScope

logger = logging.getLogger(__name__)


@dataclass
class ArcStreamState:
    """Mutable upload-tracking state shared between the ARC stream and upload handling."""

    arc_id_to_url_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    submitted: int = 0
    studies: int = 0
    assays: int = 0


def all_repositories_failed(report: HarvestReport) -> bool:
    """Return True when every repository harvest failed to produce a harvest ID."""
    return bool(report.repository_reports) and all(entry.harvest_id is None for entry in report.repository_reports)


def format_source_url_annotation(url_counts: dict[str, int]) -> str:
    """Format tracked source URLs (with occurrence counts) for a failed-record message."""
    if not url_counts:
        return ""

    parts: list[str] = []
    for url, count in sorted(url_counts.items()):
        if count > 1:
            parts.append(f"{url} (×{count})")
        else:
            parts.append(url)

    if len(parts) == 1:
        return f"source URL: {parts[0]}"
    return f"source URLs: {', '.join(parts)}"


def record_upload_outcomes(
    errors: list,
    state: ArcStreamState,
    scope: RepositoryScope,
) -> None:
    """Apply API upload results to the repository scope.

    Each per-item API error becomes ``record_failed``; the remaining submitted
    ARCs become ``record_harvested``. Study/assay totals come from all ARCs that
    were sent for upload in this completed batch.
    """
    for err in errors:
        arc_id = err.arc_id or ""
        annotation = format_source_url_annotation(state.arc_id_to_url_counts.get(arc_id, {}))
        msg = f"{err.message} — {annotation}" if annotation else err.message
        scope.record_failed(msg, record_id=err.arc_id)

    for _ in range(max(state.submitted - len(errors), 0)):
        scope.record_harvested()
    if state.studies:
        scope.add_studies(state.studies)
    if state.assays:
        scope.add_assays(state.assays)


def record_upload_aborted(
    state: ArcStreamState,
    scope: RepositoryScope,
    detail: str,
    *,
    url: str | None,
) -> None:
    """Fallback when upload aborts: count submitted ARCs as failed, not harvested."""
    for _ in range(max(state.submitted, 1)):
        scope.record_failed(detail, url=url)


def record_plugin_error(item: HarvesterError, rdi: str, scope: RepositoryScope) -> None:
    """Log a plugin-level error and record it on the repository scope."""
    if isinstance(item, RecordProcessingError):
        logger.error(
            "Processing error in repository '%s' for record '%s': %s",
            rdi,
            item.record_id,
            item,
        )
        scope.record_failed(str(item), record_id=item.record_id, url=item.url)
    else:
        logger.error("Processing error in repository '%s': %s", rdi, item)
        scope.record_failed(str(item))


def handle_skipped_record(item: SkippedRecord, rdi: str) -> None:
    """Log a skipped plugin item at INFO level (reason and URL when present)."""
    if item.url:
        logger.info("Skipped record in repository '%s': %s (url=%s)", rdi, item.reason, item.url)
    else:
        logger.info("Skipped record in repository '%s': %s", rdi, item.reason)


def emit_report(report: HarvestReport) -> None:
    """Serialize and print the finished harvest report to stdout."""
    try:
        print(JsonLdReportSerializer().render(report), end="")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to serialise harvest report: %s", exc)
