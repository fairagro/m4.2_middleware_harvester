"""CLI entrypoint for the FAIRagro Middleware Harvester."""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Callable
from pathlib import Path

from middleware.harvester.config import Config
from middleware.harvester.orchestrator import run_orchestrator
from middleware.harvester.reporting import all_repositories_failed, emit_report
from middleware.shared.tracing import initialize_logging, initialize_tracing

_SERVICE_NAME = "middleware-harvester"

logger = logging.getLogger(__name__)


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
        if all_repositories_failed(report):
            exit_code = 1
    except Exception:  # noqa: BLE001
        logger.error("Harvester run failed.")
        logger.debug("Harvester run failed.", exc_info=True)
        exit_code = 1
    finally:
        if shutdown_tracing is not None:
            shutdown_tracing()
        if report is not None:
            emit_report(report)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
