"""Abstract plugin interface shared by all harvester plugins."""

import abc
from collections.abc import AsyncGenerator

from middleware.harvester.errors import HarvesterError


class Plugin(abc.ABC):
    """Abstract base class for harvester plugins."""

    @abc.abstractmethod
    async def run(self) -> AsyncGenerator[tuple[str, str | None] | HarvesterError, None]:
        """Run the plugin and yield (arc_json, source_url) pairs or errors."""
        if False:  # pragma: no cover
            yield

    @abc.abstractmethod
    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count for the configured source."""
