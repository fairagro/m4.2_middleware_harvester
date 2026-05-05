"""Orchestrator for the FAIRagro Middleware Harvester."""

import argparse
import asyncio
import logging
from collections.abc import Callable
from pathlib import Path

from opentelemetry import trace

from middleware.api_client import ApiClient
from middleware.harvester.config import Config
from middleware.harvester.errors import HarvesterError
from middleware.inspire.plugin import run_plugin as run_inspire_plugin
from middleware.schema_org.plugin import run_plugin as run_schema_org_plugin
from middleware.shared.tracing import initialize_logging, initialize_tracing

_SERVICE_NAME = "middleware-harvester"

logger = logging.getLogger(__name__)

# Registry mapping plugin type names to their run_plugin functions.
# To add a new plugin: import its run_plugin and add an entry here.
_PLUGIN_RUNNERS = {
    "inspire": run_inspire_plugin,
    "schema_org": run_schema_org_plugin,
}


async def run_orchestrator(config: Config) -> None:
    """Execute the core harvester loop across all configured repositories."""
    tracer = trace.get_tracer(__name__)
    async with ApiClient(config.api_client) as client:
        with tracer.start_as_current_span(
            "harvest_run",
            attributes={"harvester.repository_count": len(config.repositories)},
        ):
            for repo in config.repositories:
                logger.info("Initializing plugin type: %s", repo.plugin_type)

                plugin_runner = _PLUGIN_RUNNERS.get(repo.plugin_type)
                if plugin_runner is None:
                    logger.error("Unknown repository type '%s', skipping...", repo.plugin_type)
                    continue

                with tracer.start_as_current_span(
                    "plugin_run",
                    attributes={
                        "harvester.plugin_type": repo.plugin_type,
                        "harvester.repository_rdi": repo.rdi,
                    },
                ) as plugin_span:
                    try:
                        plugin_gen = plugin_runner(repo.plugin_config)

                        count = 0
                        async for item in plugin_gen:
                            if isinstance(item, HarvesterError):
                                logger.error("Processing error in plugin '%s': %s", repo.plugin_type, item)
                                continue

                            with tracer.start_as_current_span("arc_upload") as upload_span:
                                try:
                                    response = await client.create_or_update_arc(
                                        rdi=repo.rdi,
                                        arc=item,
                                    )
                                    upload_span.set_attribute("harvester.arc_id", response.arc_id)
                                    logger.info(
                                        "Successfully uploaded %s ARC ID: %s", repo.plugin_type, response.arc_id
                                    )
                                    count += 1
                                except Exception as e:  # noqa: BLE001
                                    upload_span.set_status(trace.StatusCode.ERROR)
                                    upload_span.record_exception(e)
                                    logger.error("Failed to upload ARC for %s: %s", repo.plugin_type, e)

                        plugin_span.set_attribute("harvester.arcs_uploaded", count)
                        logger.info("Finished processing repository %s with %d ARCs uploaded.", repo.plugin_type, count)
                    except Exception as e:  # noqa: BLE001
                        plugin_span.set_status(trace.StatusCode.ERROR)
                        plugin_span.record_exception(e)
                        logger.error("Repository '%s' failed and will be skipped: %s", repo.plugin_type, e)


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
