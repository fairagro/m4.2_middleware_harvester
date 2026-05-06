"""Orchestrator for the FAIRagro Middleware Harvester."""

import argparse
import asyncio
import logging
from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from typing import TYPE_CHECKING, cast

from opentelemetry import trace

from middleware.api_client import ApiClient
from middleware.harvester.config import Config, RepositoryConfig
from middleware.harvester.errors import HarvesterError
from middleware.harvester.plugin_base import Plugin
from middleware.harvester.plugin_config import PluginConfig
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


async def _run_repository(repo: RepositoryConfig, client: ApiClient, tracer: trace.Tracer) -> None:
    logger.info("Initializing plugin type: %s", repo.plugin_type)

    plugin_cls = _PLUGIN_CLASSES.get(repo.plugin_type)
    if plugin_cls is None:
        logger.error("Unknown repository type '%s', skipping...", repo.plugin_type)
        return

    plugin_instance = cast(Callable[[PluginConfig], Plugin], plugin_cls)(repo.plugin_config)
    plugin_gen = plugin_instance.run()
    expected_datasets = await plugin_instance.get_expected_datasets()

    with tracer.start_as_current_span(
        "plugin_run",
        attributes={
            "harvester.plugin_type": repo.plugin_type,
            "harvester.repository_rdi": repo.rdi,
        },
    ) as plugin_span:
        arc_count = [0]

        async def _arc_stream(
            gen: AsyncGenerator[str | HarvesterError, None],
            plugin_type: str,
        ) -> AsyncGenerator[str, None]:
            async for item in gen:
                if isinstance(item, HarvesterError):
                    logger.error("Processing error in plugin '%s': %s", plugin_type, item)
                    continue
                arc_count[0] += 1
                yield item

        try:
            with tracer.start_as_current_span("harvest_upload") as upload_span:
                try:
                    result = await client.harvest_arcs(
                        rdi=repo.rdi,
                        arcs=_arc_stream(plugin_gen, repo.plugin_type),
                        expected_datasets=expected_datasets,
                    )
                    upload_span.set_attribute("harvester.harvest_id", result.harvest_id)
                    upload_span.set_attribute("harvester.arcs_uploaded", arc_count[0])
                    logger.info(
                        "Finished processing repository %s. Harvest: %s",
                        repo.plugin_type,
                        result.harvest_id,
                    )
                except Exception as e:
                    upload_span.set_status(trace.StatusCode.ERROR)
                    upload_span.record_exception(e)
                    raise

            plugin_span.set_attribute("harvester.harvest_id", result.harvest_id)
            plugin_span.set_attribute("harvester.arcs_uploaded", arc_count[0])
        except Exception as e:  # noqa: BLE001
            plugin_span.set_status(trace.StatusCode.ERROR)
            plugin_span.record_exception(e)
            plugin_span.set_attribute("harvester.arcs_uploaded", arc_count[0])
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

    config = Config.from_yaml_file(config_path)
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO), format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    shutdown_tracing = _init_tracing(config)
    try:
        asyncio.run(run_orchestrator(config))
    except Exception:  # noqa: BLE001
        logger.exception("Harvester run failed.")
        return 1
    finally:
        if shutdown_tracing is not None:
            shutdown_tracing()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
