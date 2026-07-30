"""Core harvest orchestration across configured repositories."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path

from opentelemetry import trace

from middleware.api_client import ApiClient
from middleware.harvester.config import Config, RepositoryConfig
from middleware.harvester.errors import (
    failure_url_for_exception,
    format_exception_for_report,
    harvest_id_from_exception,
)
from middleware.harvester.plugin_base import Plugin
from middleware.harvester.upload import execute_harvest_upload
from middleware.inspire.plugin import InspirePlugin
from middleware.linked_data.plugin import LinkedDataPlugin
from middleware.shared.report import HarvestReport

logger = logging.getLogger(__name__)

PLUGIN_FACTORIES: dict[str, Callable[..., Plugin]] = {
    "inspire": InspirePlugin,
    "linked_data": LinkedDataPlugin,
}


async def heartbeat_loop(path: Path, interval: int) -> None:
    """Touch *path* every *interval* seconds to signal liveness."""
    while True:
        try:
            path.touch()
        except OSError as e:
            logger.error("Failed to touch heartbeat file %s: %s", path, e)
        await asyncio.sleep(interval)


async def run_repository(
    repo: RepositoryConfig,
    client: ApiClient,
    tracer: trace.Tracer,
    report: HarvestReport,
) -> None:
    """Run one repository plugin and record results on ``report``."""
    logger.info("Initializing repository %s (%s)", repo.rdi, repo.plugin_type)
    scope = report.open_repository(repo.rdi)

    try:
        plugin_factory = PLUGIN_FACTORIES.get(repo.plugin_type)
        if plugin_factory is None:
            logger.error("Unknown repository type '%s' for repository '%s', skipping...", repo.plugin_type, repo.rdi)
            return

        logger.debug("Initializing plugin for repository %s (%s)", repo.rdi, repo.plugin_type)
        plugin_instance = plugin_factory(repo.plugin_config)
        plugin_gen = plugin_instance.run()
        try:
            logger.debug("Getting expected datasets for repository %s (%s)", repo.rdi, repo.plugin_type)
            expected_datasets = await plugin_instance.get_expected_datasets()
            if expected_datasets is not None:
                scope.set_expected_datasets(expected_datasets)
            logger.debug(
                "Repository %s (%s) expected datasets=%s",
                repo.rdi,
                repo.plugin_type,
                expected_datasets,
            )
            await execute_harvest_upload(
                repo,
                client,
                tracer,
                plugin_gen,
                scope,
            )
        finally:
            await plugin_gen.aclose()
    except Exception as exc:  # noqa: BLE001
        detail = format_exception_for_report(exc)
        logger.error("Unhandled exception in repository '%s', skipping: %s", repo.rdi, detail)
        logger.debug("Unhandled exception in repository '%s'.", repo.rdi, exc_info=True)
        recovered_id = harvest_id_from_exception(exc)
        if recovered_id is not None:
            scope.set_harvest_id(recovered_id)
        scope.record_failed(
            detail,
            url=failure_url_for_exception(exc) or repo.source_url,
        )
    finally:
        scope.close()


async def run_orchestrator(config: Config) -> HarvestReport:
    """Execute the core harvester loop across all configured repositories."""
    tracer = trace.get_tracer(__name__)
    report = HarvestReport()
    heartbeat_task = asyncio.create_task(heartbeat_loop(Path(config.heartbeat_path), config.heartbeat_interval))

    try:
        async with ApiClient(config.api_client) as client:
            with tracer.start_as_current_span(
                "harvest_run",
                attributes={"harvester.repository_count": len(config.repositories)},
            ):
                tasks = [
                    asyncio.create_task(run_repository(repo, client, tracer, report)) for repo in config.repositories
                ]
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for repo, result in zip(config.repositories, results, strict=True):
                        if isinstance(result, BaseException):
                            detail = format_exception_for_report(result)
                            logger.error(
                                "Repository task failed for %s (%s): %s",
                                repo.rdi,
                                repo.plugin_type,
                                detail,
                            )
                            logger.debug(
                                "Repository task exception for %s (%s).",
                                repo.rdi,
                                repo.plugin_type,
                                exc_info=result,
                            )
                            scope = report.open_repository(repo.rdi)
                            scope.record_failed(
                                detail,
                                url=failure_url_for_exception(result) or repo.source_url,
                            )
                            scope.close()
    finally:
        heartbeat_task.cancel()
        report.finish()

    return report
