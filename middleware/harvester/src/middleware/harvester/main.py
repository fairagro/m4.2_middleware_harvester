"""Orchestrator for the FAIRagro Middleware Harvester."""

import argparse
import asyncio
import logging
from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from typing import TYPE_CHECKING

from opentelemetry import trace

from middleware.api_client import ApiClient
from middleware.harvester.config import Config, RepositoryConfig
from middleware.harvester.errors import HarvesterError
from middleware.inspire import plugin as inspire_plugin
from middleware.schema_org import plugin as schema_org_plugin
from middleware.shared.tracing import initialize_logging, initialize_tracing

if TYPE_CHECKING:
    from middleware.harvester.plugin_config import PluginConfig

_SERVICE_NAME = "middleware-harvester"

logger = logging.getLogger(__name__)

# Registry mapping plugin type names to their run_plugin functions.
# To add a new plugin: import its run_plugin and add an entry here.
_PLUGIN_RUNNERS = {
    "inspire": inspire_plugin.run_plugin,
    "schema_org": schema_org_plugin.run_plugin,
}


async def _get_expected_datasets(plugin_type: str, config: "PluginConfig") -> int | None:
    """Return the expected dataset count from the plugin, if available."""
    if plugin_type == "inspire":
        return await inspire_plugin.get_expected_datasets(config)
    if plugin_type == "schema_org":
        return await schema_org_plugin.get_expected_datasets(config)
    return None


async def _run_repository(repo: RepositoryConfig, client: ApiClient, tracer: trace.Tracer) -> None:
    logger.info("Initializing plugin type: %s", repo.plugin_type)

    plugin_runner = _PLUGIN_RUNNERS.get(repo.plugin_type)
    if plugin_runner is None:
        logger.error("Unknown repository type '%s', skipping...", repo.plugin_type)
        return

    with tracer.start_as_current_span(
        "plugin_run",
        attributes={
            "harvester.plugin_type": repo.plugin_type,
            "harvester.repository_rdi": repo.rdi,
        },
    ) as plugin_span:
        try:
            plugin_gen = plugin_runner(repo.plugin_config)
            expected_datasets = await _get_expected_datasets(repo.plugin_type, repo.plugin_config)

            async def _arc_stream(
                gen: AsyncGenerator[str | HarvesterError, None],
                plugin_type: str,
            ) -> AsyncGenerator[str, None]:
                async for item in gen:
                    if isinstance(item, HarvesterError):
                        logger.error("Processing error in plugin '%s': %s", plugin_type, item)
                        continue
                    yield item

            with tracer.start_as_current_span("harvest_upload") as upload_span:
                result = await client.harvest_arcs(
                    rdi=repo.rdi,
                    arcs=_arc_stream(plugin_gen, repo.plugin_type),
                    expected_datasets=expected_datasets,
                )
                upload_span.set_attribute("harvester.harvest_id", result.harvest_id)
                logger.info(
                    "Finished processing repository %s. Harvest: %s",
                    repo.plugin_type,
                    result.harvest_id,
                )

            plugin_span.set_attribute("harvester.harvest_id", result.harvest_id)
        except Exception as e:  # noqa: BLE001
            plugin_span.set_status(trace.StatusCode.ERROR)
            plugin_span.record_exception(e)
            logger.error("Repository '%s' failed and will be skipped: %s", repo.plugin_type, e)


async def run_orchestrator(config: Config) -> None:
    """Execute the core harvester loop across all configured repositories."""
    tracer = trace.get_tracer(__name__)
    async with ApiClient(config.api_client) as client:
        with tracer.start_as_current_span(
            "harvest_run",
            attributes={"harvester.repository_count": len(config.repositories)},
        ):
            tasks = [asyncio.create_task(_run_repository(repo, client, tracer)) for repo in config.repositories]
            if not tasks:
                return

            results = await asyncio.gather(*tasks, return_exceptions=True)
            failures = [result for result in results if isinstance(result, Exception)]
            for failure in failures:
                logger.error("Repository task failed: %s", failure)
            if failures and len(failures) == len(tasks):
                raise RuntimeError("All repository tasks failed.")


def _init_tracing(config: Config) -> Callable[[], None] | None:
    """Initialise OpenTelemetry tracing and logging when an endpoint is configured.

    Returns a no-argument shutdown callable so the caller can flush pending
    spans on exit, or None when tracing is disabled.
    """
    if not config.otel.endpoint:
        return None
    provider, _ = initialize_tracing(
        service_name=_SERVICE_NAME,
        otlp_endpoint=config.otel.endpoint,
        log_console_spans=config.otel.log_console_spans,
    )
    initialize_logging(
        service_name=_SERVICE_NAME,
        otlp_endpoint=config.otel.endpoint,
        log_level=logging.getLevelName(config.log_level),
        otlp_log_level=logging.getLevelName(config.otel.log_level),
    )
    return provider.shutdown


def main() -> None:
    """CLI entry point for the Middleware Harvester."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="FAIRagro Middleware Harvester Orchestrator")
    parser.add_argument("-c", "--config", required=True, type=Path, help="Path to config file")

    args = parser.parse_args()

    try:
        config = Config.from_yaml_file(args.config)
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to load root configuration: %s", e)
        return

    shutdown = _init_tracing(config)
    try:
        asyncio.run(run_orchestrator(config))
    finally:
        if shutdown is not None:
            shutdown()


if __name__ == "__main__":
    main()
