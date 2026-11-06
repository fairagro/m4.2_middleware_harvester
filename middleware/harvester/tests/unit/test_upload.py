"""Tests for the harvest upload path: API harvest status after plugin-yielded errors."""

from collections.abc import AsyncGenerator, AsyncIterable
from types import TracebackType
from unittest.mock import MagicMock, patch

import pytest

from middleware.contracts.errors import HarvesterError, SkippedRecord
from middleware.contracts.plugin_base import HarvestedArc
from middleware.harvester.orchestrator import run_orchestrator


class FakeApiClient:
    """Mirror ``ApiClient.harvest_arcs``: fail the harvest if the stream raises, else complete it."""

    def __init__(self) -> None:
        """Start with no recorded harvest outcomes."""
        self.outcomes: list[tuple[str, str]] = []
        self.submitted: list[str] = []

    async def __aenter__(self) -> "FakeApiClient":
        """Return the client itself."""
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        """Nothing to close."""

    async def harvest_arcs(self, *, rdi: str, arcs: AsyncIterable[str], **_kwargs: object) -> MagicMock:
        """Drain ``arcs``; record ``fail`` and re-raise on error, otherwise record ``complete``."""
        try:
            async for arc in arcs:
                self.submitted.append(arc)
        except Exception:
            self.outcomes.append((rdi, "fail"))
            raise
        self.outcomes.append((rdi, "complete"))
        result = MagicMock()
        result.harvest_id = f"harvest-{rdi}"
        result.errors = []
        return result


def _make_repo(rdi: str) -> MagicMock:
    repo = MagicMock()
    repo.plugin_type = "inspire"
    repo.rdi = rdi
    repo.source_url = f"https://example.test/{rdi}"
    return repo


def _plugin_yielding(*items: HarvestedArc | HarvesterError | SkippedRecord) -> type:
    class _Plugin:
        def __init__(self, config: object, *_args: object) -> None:
            self._config = config

        async def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:  # noqa: PLR6301
            for item in items:
                yield item

        async def get_expected_datasets(self) -> int | None:  # noqa: PLR6301
            return None

    return _Plugin


@pytest.mark.asyncio
async def test_repository_error_without_arcs_fails_harvest() -> None:
    """A plugin that yields only a repository-level error ends with a FAILED API harvest."""
    config = MagicMock()
    config.repositories = [_make_repo("rdi-a")]
    client = FakeApiClient()

    with (
        patch(
            "middleware.harvester.orchestrator.PLUGIN_FACTORIES",
            {"inspire": _plugin_yielding(HarvesterError("CSW endpoint unreachable"))},
        ),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=client),
    ):
        await run_orchestrator(config)

    assert client.outcomes == [("rdi-a", "fail")]
