"""Unit tests for the Harvester orchestrator main module."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from middleware.harvester.errors import HarvesterError
from middleware.harvester.main import _run_repository, run_orchestrator
from middleware.harvester.plugin_base import Plugin
from middleware.harvester.report import HarvestReport, RepositoryReport, print_report


def _make_repo(plugin_type: str = "inspire") -> MagicMock:
    repo = MagicMock()
    repo.plugin_type = plugin_type
    repo.plugin_config = MagicMock()
    repo.rdi = f"{plugin_type}-rdi"
    return repo


def _make_mock_client() -> AsyncMock:
    client = AsyncMock()
    harvest_result = MagicMock()
    harvest_result.harvest_id = "harvest-1"
    client.harvest_arcs.return_value = harvest_result
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.mark.asyncio
async def test_plugin_factory_exception_skips_repo_and_continues() -> None:
    """If plugin_runner() itself raises on call, that repo is skipped and the next is processed."""
    repos = [_make_repo(), _make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    call_count = 0

    class FailingInitPlugin(Plugin):
        def __init__(self, config: object) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("CSW endpoint unreachable")
            self._config = config

        async def run(self) -> AsyncGenerator[str, None]:
            yield "arc-json"

        async def get_expected_datasets(self) -> int | None:
            return None

    mock_client = _make_mock_client()

    with (
        patch("middleware.harvester.main._PLUGIN_CLASSES", {"inspire": FailingInitPlugin}),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    assert mock_client.harvest_arcs.call_count == 1
    assert len(report.repository_reports) == len(repos)
    assert report.repository_reports[0].harvested_datasets is None
    assert report.repository_reports[0].failed_datasets is None


@pytest.mark.asyncio
async def test_plugin_iteration_exception_skips_repo_and_continues() -> None:
    """If harvest_arcs raises (e.g. generator error propagated), that repo is skipped and the next is processed."""
    repos = [_make_repo(), _make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    class RunnerPlugin(Plugin):
        def __init__(self, config: object) -> None:
            self._config = config

        async def run(self) -> AsyncGenerator[str, None]:
            yield "arc-json"

        async def get_expected_datasets(self) -> int | None:
            return None

    harvest_result = MagicMock()
    harvest_result.harvest_id = "harvest-1"

    harvest_call_count = 0

    async def harvest_arcs_side_effect(**_kwargs: object) -> MagicMock:
        nonlocal harvest_call_count
        harvest_call_count += 1
        if harvest_call_count == 1:
            raise RuntimeError("Network error during iteration")
        return harvest_result

    mock_client = _make_mock_client()
    mock_client.harvest_arcs.side_effect = harvest_arcs_side_effect

    with (
        patch("middleware.harvester.main._PLUGIN_CLASSES", {"inspire": RunnerPlugin}),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    # harvest_arcs was called for both repos; first raised, second succeeded
    assert mock_client.harvest_arcs.call_count == len(repos)
    assert len(report.repository_reports) == len(repos)


@pytest.mark.asyncio
async def test_harvester_error_yields_logged_and_skipped() -> None:
    """HarvesterError items yielded by the generator are logged and skipped, not uploaded."""
    repos = [_make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    class HarvesterErrorPlugin(Plugin):
        def __init__(self, config: object) -> None:
            self._config = config

        async def run(self) -> AsyncGenerator[str | HarvesterError, None]:
            yield HarvesterError("record failed")
            yield "arc-json"

        async def get_expected_datasets(self) -> int | None:
            return None

    mock_client = _make_mock_client()

    # Capture the arc_stream passed to harvest_arcs and drain it
    collected: list[str] = []

    async def capturing_harvest_arcs(**kwargs: object) -> MagicMock:
        arcs = kwargs["arcs"]
        assert hasattr(arcs, "__aiter__"), "arcs must be async iterable"
        async for item in arcs:  # type: ignore[union-attr]
            collected.append(item)  # type: ignore[arg-type]
        result: MagicMock = mock_client.harvest_arcs.return_value
        return result

    mock_client.harvest_arcs.side_effect = capturing_harvest_arcs

    with (
        patch("middleware.harvester.main._PLUGIN_CLASSES", {"inspire": HarvesterErrorPlugin}),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    # Only the valid ARC string passes through the filter, not the HarvesterError
    assert collected == ["arc-json"]
    assert mock_client.harvest_arcs.call_count == 1
    assert report.repository_reports[0].harvested_datasets == 1
    assert report.repository_reports[0].failed_datasets == 1


@pytest.mark.asyncio
async def test_run_orchestrator_gathers_repositories_and_uses_expected_datasets() -> None:
    repos = [_make_repo("inspire"), _make_repo("schema_org")]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    async def failing_runner(_config: object) -> AsyncGenerator[str, None]:
        raise RuntimeError("harvest failure")
        yield  # pragma: no cover

    mock_client = _make_mock_client()
    expected_datasets = 10
    expected_harvest_calls = 2

    class SuccessPlugin(Plugin):
        def __init__(self, config: object) -> None:
            self._config = config

        async def run(self) -> AsyncGenerator[str, None]:
            yield "arc-json"

        async def get_expected_datasets(self) -> int | None:
            return None

    class FailingPlugin(Plugin):
        def __init__(self, config: object) -> None:
            self._config = config

        async def run(self) -> AsyncGenerator[str, None]:
            raise RuntimeError("harvest failure")
            yield  # pragma: no cover

        async def get_expected_datasets(self) -> int | None:
            return None

    with (
        patch("middleware.harvester.main._PLUGIN_CLASSES", {"inspire": SuccessPlugin, "schema_org": FailingPlugin}),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
        patch.object(SuccessPlugin, "get_expected_datasets", AsyncMock(return_value=expected_datasets)),
        patch.object(FailingPlugin, "get_expected_datasets", AsyncMock(return_value=expected_datasets)),
    ):
        report = await run_orchestrator(mock_config)

    assert mock_client.harvest_arcs.call_count == expected_harvest_calls
    assert all(call.kwargs["expected_datasets"] == expected_datasets for call in mock_client.harvest_arcs.mock_calls)
    assert len(report.repository_reports) == len(repos)


@pytest.mark.asyncio
async def test_run_orchestrator_returns_when_no_repositories() -> None:
    mock_config = MagicMock()
    mock_config.repositories = []
    mock_config.api_client = MagicMock()

    mock_client = _make_mock_client()
    with patch("middleware.harvester.main.ApiClient", return_value=mock_client):
        report = await run_orchestrator(mock_config)

    assert mock_client.harvest_arcs.call_count == 0
    assert report.repository_reports == []


def test_repository_report_to_jsonld_omits_expected_datasets() -> None:
    harvested_datasets = 5
    failed_datasets = 1
    report = RepositoryReport(
        rdi="bonares",
        harvest_id="harvest-1",
        duration_seconds=12.3,
        expected_datasets=None,
        harvested_datasets=harvested_datasets,
        failed_datasets=failed_datasets,
    )
    jsonld = report.to_jsonld()

    assert jsonld["@type"] == "schema:EntryPoint"
    assert jsonld["fairagro:harvestId"] == "harvest-1"
    assert "fairagro:expectedDatasets" not in jsonld
    assert jsonld["fairagro:harvestedDatasets"] == harvested_datasets
    assert jsonld["fairagro:failedDatasets"] == failed_datasets


def test_repository_report_to_jsonld_omits_optional_counts_when_unknown() -> None:
    report = RepositoryReport(
        rdi="bonares",
        harvest_id="harvest-1",
        duration_seconds=12.3,
        expected_datasets=None,
        harvested_datasets=None,
        failed_datasets=None,
    )
    jsonld = report.to_jsonld()

    assert "fairagro:harvestedDatasets" not in jsonld
    assert "fairagro:failedDatasets" not in jsonld


def test_print_report_logs_warning_on_serialisation_failure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    report = HarvestReport(
        start_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        end_time=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        repository_reports=[],
    )

    def broken_to_jsonld(_: HarvestReport) -> dict[str, object]:
        return {"unserializable": object()}

    monkeypatch.setattr(HarvestReport, "to_jsonld", broken_to_jsonld)
    print_report(report)

    assert "Failed to serialise harvest report" in caplog.text


@pytest.mark.asyncio
async def test_run_repository_unknown_plugin_skips_repo() -> None:
    repo = _make_repo("unknown")
    mock_client = _make_mock_client()
    tracer = MagicMock()

    with patch("middleware.harvester.main.logger") as mock_logger:
        await _run_repository(repo, mock_client, tracer)

    assert mock_client.harvest_arcs.call_count == 0
    mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_run_orchestrator_returns_report_when_all_tasks_fail() -> None:
    repos = [_make_repo(), _make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    mock_client = _make_mock_client()

    async def failing_run(_repo: MagicMock, _client: AsyncMock, _tracer: MagicMock) -> RepositoryReport:
        raise RuntimeError("task failed")

    with (
        patch("middleware.harvester.main._run_repository", failing_run),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    assert len(report.repository_reports) == len(repos)
    assert all(repo.harvest_id is None for repo in report.repository_reports)
