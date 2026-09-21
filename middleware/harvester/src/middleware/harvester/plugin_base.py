"""Plugin interface for all harvester plugins."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Protocol

from middleware.harvester.errors import HarvesterError, SkippedRecord
from middleware.payload.harvested_arc import HarvestedArc

__all__ = ["HarvestedArc", "Plugin"]


class Plugin(Protocol):
    """Structural interface for harvester plugins (do not inherit).

    ``run`` is an *async generator function* at runtime (``async def`` + ``yield``).
    The Protocol stub must stay a plain ``def`` returning ``AsyncGenerator``: under
    mypy, ``async def run(...) -> AsyncGenerator`` is typed as a coroutine that
    *returns* an async generator, so ``async for x in plugin.run()`` would break.
    Concrete plugins therefore implement ``async def run`` without subclassing this
    Protocol; factories are typed as ``Callable[..., Plugin]`` and checked structurally.
    """

    def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
        """Return an async generator of harvested ARCs, errors, or skips."""
        raise NotImplementedError

    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count for the configured source."""
        raise NotImplementedError
