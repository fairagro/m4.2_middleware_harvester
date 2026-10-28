"""A repository-level plugin error fails the API harvest (#546)."""

import logging
from collections.abc import AsyncGenerator, AsyncIterable
from unittest.mock import MagicMock, patch

import pytest

from middleware.contracts.errors import HarvesterError, RecordProcessingError
from middleware.contracts.plugin_base import HarvestedArc
from middleware.harvester.orchestrator import run_orchestrator
from middleware.shared.report import HarvestReport, IssueKind

from .test_main import _make_repo


class FakeApiClient:
    """Mirror ``ApiClient.harvest_arcs``: fail and re-raise on a stream error, else complete."""

    def __init__(self) -> None:
        """Start with no harvests."""
        self.outcomes: dict[str, str] = {}
        self.submitted: dict[str, list[str]] = {}

    async def __aenter__(self) -> "FakeApiClient":
        """Return the client itself."""
        return self

    async def __aexit__(self, *_exc: object) -> None:
        """Nothing to release."""

    async def harvest_arcs(self, *, rdi: str, arcs: AsyncIterable[str], **_kwargs: object) -> MagicMock:
        """Drain ``arcs`` and record whether the harvest was completed or failed."""
        harvest_id = f"harvest-{rdi}"
        self.submitted[rdi] = []
        try:
            async for arc in arcs:
                self.submitted[rdi].append(arc)
        except Exception:
            self.outcomes[rdi] = "fail"
            raise
        self.outcomes[rdi] = "complete"
        result = MagicMock()
        result.harvest_id = harvest_id
        result.errors = []
        return result


def _plugin(*items: HarvestedArc | HarvesterError) -> type:
    class ScriptedPlugin:
        def __init__(self, config: object, _mapper_config: object | None = None) -> None:
            self._config = config

        async def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError, None]:  # noqa: PLR6301
            for item in items:
                yield item

        async def get_expected_datasets(self) -> int | None:  # noqa: PLR6301
            return None

    return ScriptedPlugin


async def _run(repos: list[MagicMock], factories: dict[str, type], client: FakeApiClient) -> HarvestReport:
    config = MagicMock()
    config.repositories = repos
    config.api_client = MagicMock()
    with (
        patch("middleware.harvester.orchestrator.PLUGIN_FACTORIES", factories),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=client),
    ):
        return await run_orchestrator(config)


@pytest.mark.asyncio
async def test_repository_error_without_arcs_fails_harvest() -> None:
    """T1/T2: a discovery failure and no ARCs fails the harvest instead of completing it."""
    client = FakeApiClient()
    repo = _make_repo()

    report = await _run([repo], {"inspire": _plugin(HarvesterError("Protocol discovery failed"))}, client)

    assert client.outcomes[repo.rdi] == "fail"
    entry = report.repository_reports[0]
    assert entry.harvested_datasets == 0
    assert entry.failed_datasets == 0
    assert [f.kind for f in entry.failures] == [IssueKind.REPOSITORY]
    assert entry.failures[0].message == "Protocol discovery failed"


@pytest.mark.asyncio
async def test_repository_error_after_arcs_fails_harvest_and_keeps_counts() -> None:
    """T3: ARCs submitted before the error count as harvested; one repository issue only."""
    client = FakeApiClient()
    repo = _make_repo()
    plugin = _plugin(
        HarvestedArc(arc_json="arc-1", studies=1, assays=1),
        HarvestedArc(arc_json="arc-2", studies=1, assays=1),
        HarvesterError("Protocol discovery failed"),
    )

    report = await _run([repo], {"inspire": plugin}, client)

    assert client.outcomes[repo.rdi] == "fail"
    assert client.submitted[repo.rdi] == ["arc-1", "arc-2"]
    entry = report.repository_reports[0]
    assert entry.harvested_datasets == 2
    assert entry.failed_datasets == 0
    assert entry.total_studies == 2
    assert entry.total_assays == 2
    assert [f.kind for f in entry.failures] == [IssueKind.REPOSITORY]


@pytest.mark.asyncio
async def test_record_level_errors_only_complete_harvest() -> None:
    """T4: a ``RecordProcessingError`` alone keeps the harvest COMPLETED."""
    client = FakeApiClient()
    repo = _make_repo()
    plugin = _plugin(
        HarvestedArc(arc_json="arc-1"),
        RecordProcessingError("bad record", record_id="r2"),
    )

    report = await _run([repo], {"inspire": plugin}, client)

    assert client.outcomes[repo.rdi] == "complete"
    entry = report.repository_reports[0]
    assert entry.harvested_datasets == 1
    assert entry.failed_datasets == 1


@pytest.mark.asyncio
async def test_repository_failure_is_logged_and_other_repositories_complete(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """T5: ERROR log names the RDI and reason; the next repository still completes."""
    client = FakeApiClient()
    broken, healthy = _make_repo("inspire"), _make_repo("linked_data")
    factories = {
        "inspire": _plugin(HarvesterError("Protocol discovery failed")),
        "linked_data": _plugin(HarvestedArc(arc_json="arc-1")),
    }

    with caplog.at_level(logging.ERROR):
        report = await _run([broken, healthy], factories, client)

    assert client.outcomes == {broken.rdi: "fail", healthy.rdi: "complete"}
    failed = [r.getMessage() for r in caplog.records if "repository-level error" in r.getMessage()]
    assert len(failed) == 1
    assert broken.rdi in failed[0]
    assert "Protocol discovery failed" in failed[0]
    assert caplog.records[[r.getMessage() for r in caplog.records].index(failed[0])].levelno == logging.ERROR
    assert report.repository_reports[1].harvested_datasets == 1
    assert report.repository_reports[1].failures == ()
