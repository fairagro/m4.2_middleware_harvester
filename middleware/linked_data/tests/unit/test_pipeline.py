"""Unit tests for the Linked Data bounded pipeline plumbing."""

from collections.abc import AsyncGenerator

import pytest

from middleware.harvester.errors import HarvesterError, RecordProcessingError, SkippedRecord
from middleware.harvester.plugin_base import HarvestedArc
from middleware.linked_data.dataset import DiscoveryResult, UrlDiscoveryResult
from middleware.linked_data.pipeline import run_bounded_pipeline


async def _empty_discover() -> AsyncGenerator[UrlDiscoveryResult, None]:
    if False:  # pragma: no cover - make this an async generator
        yield UrlDiscoveryResult("https://example.org/unused")


async def _unused_process(
    _discovery_result: DiscoveryResult,
) -> list[HarvestedArc | RecordProcessingError | SkippedRecord]:
    return []


def _unused_discovery_error(exc: BaseException) -> HarvesterError:
    return HarvesterError(str(exc))


@pytest.mark.asyncio
@pytest.mark.parametrize("worker_tasks", [0, -1])
async def test_run_bounded_pipeline_rejects_non_positive_worker_tasks(worker_tasks: int) -> None:
    """Invalid worker_tasks must fail fast instead of deadlocking on Semaphore(0)."""
    agen = run_bounded_pipeline(
        discover=_empty_discover(),
        process=_unused_process,
        on_discovery_error=_unused_discovery_error,
        worker_tasks=worker_tasks,
    )
    with pytest.raises(ValueError, match="worker_tasks must be >= 1"):
        await anext(agen)
