"""Bounded discovery→worker→consumer pipeline for the Linked Data plugin.

Separates asyncio backpressure / cancellation mechanics from domain processing
in ``plugin.py``.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncGenerator, AsyncIterable, Awaitable, Callable
from dataclasses import dataclass, field

import httpx

from middleware.harvester.errors import HarvesterError, RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import RobotsTxtDisallowedError
from middleware.harvester.plugin_base import HarvestedArc

from .dataset import DiscoveryResult
from .errors import LinkedDataError

PipelineResult = HarvestedArc | HarvesterError | SkippedRecord
ProcessFn = Callable[
    [DiscoveryResult],
    Awaitable[list[HarvestedArc | RecordProcessingError | SkippedRecord]],
]
DiscoveryErrorFn = Callable[[BaseException], HarvesterError]
DiscoveryStream = AsyncIterable[DiscoveryResult | RecordProcessingError | SkippedRecord]

_DISCOVERY_EXCEPTIONS: tuple[type[BaseException], ...] = (
    LinkedDataError,
    RobotsTxtDisallowedError,
    RuntimeError,
    ValueError,
    OSError,
    httpx.HTTPError,
)


class _PipelineComplete:
    """Sentinel: discovery finished and no workers remain."""


_PIPELINE_COMPLETE = _PipelineComplete()
_PipelineQueue = asyncio.Queue[PipelineResult | _PipelineComplete]
ResultsQueueHook = Callable[[_PipelineQueue], None]


@dataclass
class _PipelineRun:
    """Mutable state shared by discovery, workers, and the yield loop."""

    discovery_finished: bool = False
    active_workers: int = 0
    complete_signaled: bool = False
    shutdown: asyncio.Event = field(default_factory=asyncio.Event)
    pipeline_tasks: list[asyncio.Task[None]] = field(default_factory=list)

    def request_shutdown(self) -> None:
        """Signal shutdown and cancel all pipeline tasks."""
        self.shutdown.set()
        # Copy: done-callbacks prune the live list while we cancel.
        for task in list(self.pipeline_tasks):
            task.cancel()

    def track_task(self, task: asyncio.Task[None]) -> None:
        """Register a pipeline task and prune it when it completes."""
        self.pipeline_tasks.append(task)

        def _prune(done: asyncio.Task[None]) -> None:
            with contextlib.suppress(ValueError):
                self.pipeline_tasks.remove(done)

        task.add_done_callback(_prune)


@dataclass
class _PipelineContext:
    """Shared queue and concurrency handles for one pipeline run."""

    results: _PipelineQueue
    semaphore: asyncio.Semaphore
    task_group: asyncio.TaskGroup
    run: _PipelineRun
    process: ProcessFn
    on_discovery_error: DiscoveryErrorFn


async def _signal_complete_if_idle(ctx: _PipelineContext) -> None:
    """Unblock the consumer when discovery is done and no workers remain.

    Skipped when shutdown is already set: the consumer has left and must not
    block a cancelled worker on a full queue waiting to enqueue the sentinel.
    """
    run = ctx.run
    if not run.discovery_finished or run.active_workers > 0 or run.complete_signaled:
        return
    run.complete_signaled = True
    if run.shutdown.is_set():
        return
    await ctx.results.put(_PIPELINE_COMPLETE)


async def _run_pipeline_worker(
    discovery_result: DiscoveryResult,
    ctx: _PipelineContext,
) -> None:
    """Process one discovery item and enqueue each mapped outcome."""
    # Always release the permit and decrement the counter, including on
    # CancelledError — otherwise the consumer can deadlock waiting for
    # active_workers to reach 0 while results.get() never completes.
    try:
        for result in await ctx.process(discovery_result):
            await ctx.results.put(result)
    finally:
        ctx.run.active_workers -= 1
        ctx.semaphore.release()
        await _signal_complete_if_idle(ctx)


async def _run_discovery_producer(
    discover: DiscoveryStream,
    ctx: _PipelineContext,
) -> None:
    """Consume discovery and spawn bounded worker tasks."""
    try:
        async for item in discover:
            if ctx.run.shutdown.is_set():
                break
            # Inspire-style: discovery already yields shared harvester signals.
            if isinstance(item, (RecordProcessingError, SkippedRecord)):
                await ctx.results.put(item)
                continue
            await ctx.semaphore.acquire()
            if ctx.run.shutdown.is_set():
                ctx.semaphore.release()
                break
            ctx.run.active_workers += 1
            ctx.run.track_task(
                ctx.task_group.create_task(_run_pipeline_worker(item, ctx)),
            )
    except _DISCOVERY_EXCEPTIONS as exc:
        # Discovery-level failure must not escape TaskGroup as ExceptionGroup;
        # yield a HarvesterError so the orchestrator can report it cleanly.
        if not ctx.run.shutdown.is_set():
            await ctx.results.put(ctx.on_discovery_error(exc))
    finally:
        ctx.run.discovery_finished = True
        await _signal_complete_if_idle(ctx)


async def _stream_pipeline_results(
    results: _PipelineQueue,
) -> AsyncGenerator[PipelineResult, None]:
    """Yield queued outcomes until the idle sentinel arrives."""
    while True:
        item = await results.get()
        if isinstance(item, _PipelineComplete):
            return
        yield item


async def run_bounded_pipeline(
    *,
    discover: DiscoveryStream,
    process: ProcessFn,
    on_discovery_error: DiscoveryErrorFn,
    worker_tasks: int,
    on_results_queue: ResultsQueueHook | None = None,
) -> AsyncGenerator[PipelineResult, None]:
    """Run a bounded producer/worker/consumer pipeline and yield outcomes.

    At most ``worker_tasks`` results may sit in the queue and ``worker_tasks``
    workers may run concurrently (``2 × worker_tasks`` discovery items in
    workers plus queue slots). One discovery item may still map to multiple
    outcomes. Closing the returned generator cancels in-flight work.

    ``worker_tasks`` must be >= 1. ``Semaphore(0)`` would deadlock discovery;
    ``Queue(maxsize=0)`` is unbounded in asyncio and would disable backpressure.

    ``on_results_queue`` is an optional test/observability hook invoked once with
    the bounded results queue after creation.
    """
    if worker_tasks < 1:
        raise ValueError(f"worker_tasks must be >= 1, got {worker_tasks}")

    results: _PipelineQueue = asyncio.Queue(maxsize=worker_tasks)
    if on_results_queue is not None:
        on_results_queue(results)
    semaphore = asyncio.Semaphore(worker_tasks)
    run = _PipelineRun()

    async with asyncio.TaskGroup() as task_group:
        ctx = _PipelineContext(
            results=results,
            semaphore=semaphore,
            task_group=task_group,
            run=run,
            process=process,
            on_discovery_error=on_discovery_error,
        )
        run.track_task(task_group.create_task(_run_discovery_producer(discover, ctx)))
        try:
            async for payload in _stream_pipeline_results(results):
                yield payload
        except GeneratorExit:
            # Also covers aclose while suspended in results.get(), not only at yield.
            run.request_shutdown()
            return
        finally:
            run.shutdown.set()
