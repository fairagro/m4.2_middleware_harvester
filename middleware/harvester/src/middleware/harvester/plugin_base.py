"""Plugin interface for all harvester plugins."""

from collections.abc import AsyncGenerator
from typing import Protocol

from middleware.harvester.errors import HarvesterError


class Plugin(Protocol):
    """Protocol defining the harvester plugin interface."""

    def run(self) -> AsyncGenerator[tuple[str, str | None] | HarvesterError, None]:
        """Run the plugin and yield (arc_json, source_url) pairs or errors."""
        pass  # noqa: PIE790

    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count for the configured source."""
        pass  # noqa: PIE790
