"""Upload ARCs from a plugin stream to the Middleware API."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from middleware.api_client import ApiClient
from middleware.contracts.errors import HarvesterError, RecordProcessingError, SkippedRecord
from middleware.contracts.plugin_base import HarvestedArc
from middleware.harvester.config import RepositoryConfig
from middleware.harvester.errors import (
    failure_url_for_exception,
    format_exception_for_report,
    harvest_id_from_exception,
)
from middleware.harvester.reporting import (
    ArcStreamState,
    handle_skipped_record,
    record_plugin_error,
    record_upload_aborted,
    record_upload_outcomes,
)
from middleware.shared.report import RepositoryScope

logger = logging.getLogger(__name__)


class RepositoryErrorRecorded(Exception):  # noqa: N818
    """Raised at the end of the ARC stream so ``harvest_arcs`` fails the harvest.

    The plugin's repository-level error is already on the scope; this is not an
    upload abort.
    """


async def arc_stream(
    gen: AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None],
    rdi: str,
    scope: RepositoryScope,
    state: ArcStreamState,
) -> AsyncGenerator[str, None]:
    """Filter the plugin stream and track submitted ARC composition for reporting.

    Raises:
        RepositoryErrorRecorded: After the plugin stream ends, when it yielded a
            repository-level ``HarvesterError``.
    """
    async for item in gen:
        if isinstance(item, SkippedRecord):
            scope.record_skipped()
            handle_skipped_record(item, rdi)
            continue
        if isinstance(item, HarvesterError):
            record_plugin_error(item, rdi, scope)
            if not isinstance(item, RecordProcessingError):
                state.repository_error = str(item)
            continue
        if item.source_url is not None and item.identifier:
            counts = state.arc_id_to_url_counts.setdefault(item.identifier, {})
            counts[item.source_url] = counts.get(item.source_url, 0) + 1
        state.submitted += 1
        state.studies += item.studies
        state.assays += item.assays
        yield item.arc_json
    if state.repository_error is not None:
        raise RepositoryErrorRecorded(state.repository_error)


async def execute_harvest_upload(
    repo: RepositoryConfig,
    client: ApiClient,
    tracer: trace.Tracer,
    plugin_gen: AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None],
    scope: RepositoryScope,
) -> None:
    """Upload ARCs from ``plugin_gen`` and record outcomes on ``scope``."""
    state = ArcStreamState()
    harvest_id: str | None = None
    expected_datasets = scope.snapshot().expected_datasets

    with tracer.start_as_current_span(
        "plugin_run",
        attributes={
            "harvester.plugin_type": repo.plugin_type,
            "harvester.repository_rdi": repo.rdi,
        },
    ) as plugin_span:
        try:
            with tracer.start_as_current_span("harvest_upload") as upload_span:
                try:
                    logger.debug(
                        "Begin upload for repository %s (%s) with expected_datasets=%s",
                        repo.rdi,
                        repo.plugin_type,
                        expected_datasets,
                    )
                    result = await client.harvest_arcs(
                        rdi=repo.rdi,
                        arcs=arc_stream(plugin_gen, repo.rdi, scope, state),
                        expected_datasets=expected_datasets,
                    )
                    harvest_id = result.harvest_id
                    scope.set_harvest_id(harvest_id)
                    record_upload_outcomes(result.errors, state, scope)
                    upload_span.set_attribute("harvester.harvest_id", harvest_id)
                    upload_span.set_attribute(
                        "harvester.arcs_uploaded",
                        scope.snapshot().harvested_datasets,
                    )
                    logger.info(
                        "Finished processing repository %s (%s). Harvest: %s",
                        repo.rdi,
                        repo.plugin_type,
                        harvest_id,
                    )
                except Exception as e:
                    upload_span.set_status(Status(StatusCode.ERROR))
                    upload_span.record_exception(e)
                    # harvest_arcs creates the harvest before uploading; recover the
                    # id from the error when the call raises instead of returning.
                    if harvest_id is None:
                        harvest_id = harvest_id_from_exception(e)
                    if harvest_id is not None:
                        scope.set_harvest_id(harvest_id)
                        upload_span.set_attribute("harvester.harvest_id", harvest_id)
                    if isinstance(e, RepositoryErrorRecorded):
                        raise
                    logger.error(
                        "Error uploading arcs for repository %s (%s): %s",
                        repo.rdi,
                        repo.plugin_type,
                        format_exception_for_report(e),
                    )
                    logger.debug(
                        "Exception during harvest upload for repository %s (%s).",
                        repo.rdi,
                        repo.plugin_type,
                        exc_info=e,
                    )
                    raise

            if harvest_id is not None:
                plugin_span.set_attribute("harvester.harvest_id", harvest_id)
            plugin_span.set_attribute(
                "harvester.arcs_uploaded",
                scope.snapshot().harvested_datasets,
            )
        except Exception as e:  # noqa: BLE001
            plugin_span.set_status(Status(StatusCode.ERROR))
            plugin_span.record_exception(e)
            if harvest_id is None:
                harvest_id = harvest_id_from_exception(e)
            if harvest_id is not None:
                scope.set_harvest_id(harvest_id)
                plugin_span.set_attribute("harvester.harvest_id", harvest_id)
            if isinstance(e, RepositoryErrorRecorded):
                # harvest_arcs returns no per-item errors when it raises, so
                # every submitted ARC counts as harvested.
                record_upload_outcomes([], state, scope)
                plugin_span.set_attribute("harvester.arcs_uploaded", scope.snapshot().harvested_datasets)
                logger.error(
                    "Harvest %s for repository '%s' (%s) failed after a repository-level error: %s",
                    harvest_id or "(id unknown)",
                    repo.rdi,
                    repo.plugin_type,
                    e,
                )
                return
            plugin_span.set_attribute(
                "harvester.arcs_uploaded",
                scope.snapshot().harvested_datasets,
            )
            detail = format_exception_for_report(e)
            logger.error("Repository '%s' (%s) failed and will be skipped: %s", repo.rdi, repo.plugin_type, detail)
            logger.debug(
                "Repository '%s' (%s) failed and will be skipped.",
                repo.rdi,
                repo.plugin_type,
                exc_info=e,
            )
            record_upload_aborted(
                state,
                scope,
                detail,
                url=failure_url_for_exception(e) or repo.source_url,
            )
