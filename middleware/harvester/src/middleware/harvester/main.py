"""Orchestrator for the FAIRagro Middleware Harvester."""

import argparse
import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

from opentelemetry import trace

from middleware.api_client import ApiClient
from middleware.api_client.models import HarvestErrorType
from middleware.harvester.config import Config, RepositoryConfig
from middleware.harvester.errors import HarvesterError, RecordProcessingError
from middleware.harvester.plugin_base import Plugin
from middleware.harvester.plugin_config import PluginConfig
from middleware.harvester.report import FailedRecord, HarvestReport, RepositoryReport, print_report
from middleware.inspire.plugin import InspirePlugin
from middleware.schema_org.plugin import SchemaOrgPlugin
from middleware.shared.tracing import initialize_logging, initialize_tracing

if TYPE_CHECKING:
    pass

_SERVICE_NAME = "middleware-harvester"

logger = logging.getLogger(__name__)

_PLUGIN_CLASSES: dict[str, type[Plugin]] = {
    "inspire": InspirePlugin,
    "schema_org": SchemaOrgPlugin,
}


def _extract_arc_identifier(arc_json: str) -> str | None:
    """Extract the RO-Crate identifier from a serialized ARC JSON string."""
    graph = json.loads(arc_json).get("@graph")
    if isinstance(graph, list):
        for item in graph:
            if isinstance(item, dict) and item.get("@id") == "./":
                identifier = item.get("identifier")
                if isinstance(identifier, list):
                    identifier = identifier[0] if identifier else None
                return str(identifier) if identifier else None
    return None


def _apply_client_errors(
    errors: list,
    arc_id_to_url: dict[str, str],
    harvested_datasets: int | None,
    failed_datasets: int | None,
    failed_records: list[FailedRecord],
) -> tuple[int | None, int | None]:
    """Translate api_client-level HarvestErrors into harvester report counters."""
    for err in errors:
        if err.error_type == HarvestErrorType.DUPLICATE and harvested_datasets is not None and harvested_datasets > 0:
            harvested_datasets -= 1
        if failed_datasets is None:
            failed_datasets = 0
        failed_datasets += 1
        arc_id = err.arc_id or ""
        url = arc_id_to_url.get(arc_id)
        msg = f"{err.message} — source URL: {url}" if url else err.message
        failed_records.append(FailedRecord(message=msg, record_id=err.arc_id))
    return harvested_datasets, failed_datasets


def _handle_plugin_error(
    item: HarvesterError,
    plugin_type: str,
    failed_records: list[FailedRecord],
) -> None:
    """Log a plugin-level error and append a FailedRecord."""
    if isinstance(item, RecordProcessingError):
        logger.error(
            "Processing error in plugin '%s' for record '%s': %s",
            plugin_type,
            item.record_id,
            item,
        )
        failed_records.append(FailedRecord(message=str(item), record_id=item.record_id, url=item.url))
    else:
        logger.error("Processing error in plugin '%s': %s", plugin_type, item)
        failed_records.append(FailedRecord(message=str(item)))


async def _execute_harvest_upload(  # noqa: C901
    repo: RepositoryConfig,
    client: ApiClient,
    tracer: trace.Tracer,
    plugin_gen: AsyncGenerator[tuple[str, str | None] | HarvesterError, None],
    expected_datasets: int | None,
) -> tuple[str | None, int | None, int | None, bool, list[FailedRecord]]:
    harvest_id: str | None = None
    harvested_datasets: int | None = None
    failed_datasets: int | None = None
    harvest_started = False
    failed_records: list[FailedRecord] = []
    arc_id_to_url: dict[str, str] = {}

    with tracer.start_as_current_span(
        "plugin_run",
        attributes={
            "harvester.plugin_type": repo.plugin_type,
            "harvester.repository_rdi": repo.rdi,
        },
    ) as plugin_span:

        async def _arc_stream(
            gen: AsyncGenerator[tuple[str, str | None] | HarvesterError, None],
            plugin_type: str,
        ) -> AsyncGenerator[str, None]:
            nonlocal harvested_datasets, failed_datasets
            async for item in gen:
                if isinstance(item, HarvesterError):
                    if failed_datasets is None:
                        failed_datasets = 0
                    failed_datasets += 1
                    _handle_plugin_error(item, plugin_type, failed_records)
                    continue
                arc_json, source_url = item
                if source_url is not None:
                    try:
                        arc_id = _extract_arc_identifier(arc_json)
                        if arc_id:
                            arc_id_to_url[arc_id] = source_url
                    except Exception:  # noqa: BLE001
                        pass
                if harvested_datasets is None:
                    harvested_datasets = 0
                harvested_datasets += 1
                yield arc_json

        try:
            with tracer.start_as_current_span("harvest_upload") as upload_span:
                harvest_started = True
                try:
                    result = await client.harvest_arcs(
                        rdi=repo.rdi,
                        arcs=_arc_stream(plugin_gen, repo.plugin_type),
                        expected_datasets=expected_datasets,
                    )
                    harvest_id = result.harvest_id
                    harvested_datasets, failed_datasets = _apply_client_errors(
                        result.errors,
                        arc_id_to_url,
                        harvested_datasets,
                        failed_datasets,
                        failed_records,
                    )
                    upload_span.set_attribute("harvester.harvest_id", harvest_id)
                    upload_span.set_attribute(
                        "harvester.arcs_uploaded",
                        harvested_datasets if harvested_datasets is not None else 0,
                    )
                    logger.info(
                        "Finished processing repository %s. Harvest: %s",
                        repo.plugin_type,
                        harvest_id,
                    )
                except Exception as e:
                    upload_span.set_status(trace.StatusCode.ERROR)
                    upload_span.record_exception(e)
                    raise

            if harvest_id is not None:
                plugin_span.set_attribute("harvester.harvest_id", harvest_id)
            plugin_span.set_attribute(
                "harvester.arcs_uploaded",
                harvested_datasets if harvested_datasets is not None else 0,
            )
        except Exception as e:  # noqa: BLE001
            plugin_span.set_status(trace.StatusCode.ERROR)
            plugin_span.record_exception(e)
            plugin_span.set_attribute(
                "harvester.arcs_uploaded",
                harvested_datasets if harvested_datasets is not None else 0,
            )
            logger.error("Repository '%s' failed and will be skipped: %s", repo.plugin_type, e)

    return harvest_id, harvested_datasets, failed_datasets, harvest_started, failed_records


async def _run_repository(repo: RepositoryConfig, client: ApiClient, tracer: trace.Tracer) -> RepositoryReport:
    logger.info("Initializing plugin type: %s", repo.plugin_type)
    start_time = datetime.now(UTC)

    expected_datasets: int | None = None
    harvested_datasets: int | None = None
    failed_datasets: int | None = None
    harvest_started = False
    harvest_id: str | None = None
    unhandled_failure = False
    failed_records: list[FailedRecord] = []

    plugin_cls = _PLUGIN_CLASSES.get(repo.plugin_type)
    if plugin_cls is None:
        logger.error("Unknown repository type '%s', skipping...", repo.plugin_type)
        return RepositoryReport(
            rdi=repo.rdi,
            harvest_id=None,
            duration_seconds=0.0,
            expected_datasets=None,
            harvested_datasets=None,
            failed_datasets=None,
        )

    try:
        plugin_instance = cast(Callable[[PluginConfig], Plugin], plugin_cls)(repo.plugin_config)
        plugin_gen = plugin_instance.run()
        try:
            expected_datasets = await plugin_instance.get_expected_datasets()
            (
                harvest_id,
                harvested_datasets,
                failed_datasets,
                harvest_started,
                failed_records,
            ) = await _execute_harvest_upload(
                repo,
                client,
                tracer,
                plugin_gen,
                expected_datasets,
            )
        finally:
            await plugin_gen.aclose()
    except Exception:  # noqa: BLE001
        logger.error("Unhandled exception in repository '%s', skipping.", repo.rdi)
        logger.debug("Unhandled exception in repository '%s'.", repo.rdi, exc_info=True)
        unhandled_failure = True

    if harvest_started:
        if harvested_datasets is None:
            harvested_datasets = 0
        if failed_datasets is None:
            failed_datasets = 0

    duration_seconds = (datetime.now(UTC) - start_time).total_seconds()
    if unhandled_failure and not harvest_started:
        failed_datasets = None
        harvested_datasets = None

    return RepositoryReport(
        rdi=repo.rdi,
        harvest_id=harvest_id,
        duration_seconds=duration_seconds,
        expected_datasets=expected_datasets,
        harvested_datasets=harvested_datasets,
        failed_datasets=failed_datasets,
        failed_records=tuple(failed_records),
    )


async def _heartbeat_loop(path: Path, interval: int) -> None:
    """Touch *path* every *interval* seconds to signal liveness."""
    path.touch()
    while True:
        await asyncio.sleep(interval)
        path.touch()


async def run_orchestrator(config: Config) -> HarvestReport:
    """Execute the core harvester loop across all configured repositories."""
    tracer = trace.get_tracer(__name__)
    start_time = datetime.now(UTC)
    heartbeat_task = asyncio.create_task(_heartbeat_loop(Path(config.heartbeat_path), config.heartbeat_interval))
    repository_reports: list[RepositoryReport] = []

    async with ApiClient(config.api_client) as client:
        with tracer.start_as_current_span(
            "harvest_run",
            attributes={"harvester.repository_count": len(config.repositories)},
        ):
            tasks = [asyncio.create_task(_run_repository(repo, client, tracer)) for repo in config.repositories]
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for repo, result in zip(config.repositories, results, strict=True):
                    if isinstance(result, Exception):
                        logger.error("Repository task failed: %s", result)
                        repository_reports.append(
                            RepositoryReport(
                                rdi=repo.rdi,
                                harvest_id=None,
                                duration_seconds=0.0,
                                expected_datasets=None,
                                harvested_datasets=0,
                                failed_datasets=None,
                            )
                        )
                    else:
                        repository_reports.append(cast(RepositoryReport, result))

    heartbeat_task.cancel()
    end_time = datetime.now(UTC)
    return HarvestReport(start_time=start_time, end_time=end_time, repository_reports=repository_reports)


def _init_tracing(config: Config) -> Callable[[], None] | None:
    """Initialise OpenTelemetry tracing and logging when an endpoint is configured.

    Returns a no-argument shutdown callable so the caller can flush pending
    spans on exit, or None when tracing is disabled.
    """
    if not config.otel.endpoint:
        return None
    log_level = getattr(logging, config.otel.log_level)
    provider, _ = initialize_tracing(_SERVICE_NAME, config.otel.endpoint, config.otel.log_console_spans)
    initialize_logging(_SERVICE_NAME, config.otel.endpoint, config.otel.log_console_spans, log_level, log_level)
    return provider.shutdown


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the FAIRagro Middleware Harvester.")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to the harvester YAML configuration file.",
    )
    return parser.parse_args()


def main() -> int:
    """Parse CLI args, load config, and run the harvester."""
    args = _parse_args()
    config_path = Path(args.config)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    shutdown_tracing = None
    report = None
    exit_code = 0
    try:
        config = Config.from_yaml_file(config_path)
        logging.getLogger().setLevel(getattr(logging, config.log_level, logging.INFO))
        shutdown_tracing = _init_tracing(config)
        report = asyncio.run(run_orchestrator(config))
        if report.all_failed:
            exit_code = 1
    except Exception:  # noqa: BLE001
        logger.error("Harvester run failed.")
        logger.debug("Harvester run failed.", exc_info=True)
        exit_code = 1
    finally:
        if shutdown_tracing is not None:
            shutdown_tracing()
        if report is not None:
            print_report(report)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
