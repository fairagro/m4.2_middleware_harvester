"""Bounded discovery→worker→consumer pipeline — re-export from ``middleware.generic``.

Kept as the linked_data import path so existing tests and ``plugin.py`` stay stable.
"""

from middleware.generic.pipeline import (  # noqa: F401
    PipelineResult,
    ResultsQueueHook,
    run_bounded_pipeline,
)

__all__ = ["PipelineResult", "ResultsQueueHook", "run_bounded_pipeline"]
