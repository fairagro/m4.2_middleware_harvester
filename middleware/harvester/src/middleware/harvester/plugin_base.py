"""Plugin interface for all harvester plugins."""

from collections.abc import AsyncGenerator
from typing import Protocol

from middleware.harvester.errors import HarvesterError, SkippedRecord


class Plugin(Protocol):
    """Protocol defining the harvester plugin interface."""

    def run(self) -> AsyncGenerator[tuple[str, str | None] | HarvesterError | SkippedRecord, None]:
        """Run the plugin and yield (arc_json, source_url) pairs, errors, or skips."""
        raise NotImplementedError

    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count for the configured source."""
        raise NotImplementedError
