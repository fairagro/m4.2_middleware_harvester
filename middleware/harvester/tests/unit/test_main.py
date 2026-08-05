"""Unit tests for the Harvester orchestrator and CLI entrypoint."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator, AsyncIterable
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from arctrl import ARC, ArcAssay, ArcInvestigation, ArcStudy

from middleware.api_client.api_client import ApiClientError
from middleware.harvester.errors import HarvesterError, SkippedRecord
from middleware.harvester.main import main
from middleware.harvester.orchestrator import run_orchestrator, run_repository
from middleware.harvester.plugin_base import HarvestedArc, Plugin
from middleware.harvester.reporting import emit_report
from middleware.shared.report import HarvestReport, JsonLdReportSerializer


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
    harvest_result.errors = []
    client.harvest_arcs.return_value = harvest_result
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


class SuccessPlugin(Plugin):
    """A plugin that yields one ARC payload successfully."""

    def __init__(self, config: object) -> None:
        """Initialize the success plugin with its configuration."""
        self._config = config

    def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
        """Yield one valid ARC payload."""

        async def generator() -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
            yield HarvestedArc(arc_json="arc-json")

        return generator()

    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count for this plugin."""
        return None


class FailingPlugin(Plugin):
    """A plugin that fails during iteration."""

    def __init__(self, config: object) -> None:
        """Initialize the failing plugin with its configuration."""
        self._config = config

    def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
        """Yield a generator that immediately raises during iteration."""

        async def generator() -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
            raise RuntimeError("harvest failure")
            yield  # pragma: no cover

        return generator()

    async def get_expected_datasets(self) -> int | None:
        """Return the expected dataset count for this plugin."""
        return None


async def _run_orchestrator_with_test_plugins(
    mock_config: MagicMock,
    mock_client: AsyncMock,
    expected_datasets: int,
) -> HarvestReport:
    with (
        patch(
            "middleware.harvester.orchestrator.PLUGIN_FACTORIES",
            {"inspire": SuccessPlugin, "linked_data": FailingPlugin},
        ),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client),
        patch.object(SuccessPlugin, "get_expected_datasets", AsyncMock(return_value=expected_datasets)),
        patch.object(FailingPlugin, "get_expected_datasets", AsyncMock(return_value=expected_datasets)),
    ):
        return await run_orchestrator(mock_config)


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

        def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
            async def generator() -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
                yield HarvestedArc(arc_json="arc-json")

            return generator()

        async def get_expected_datasets(self) -> int | None:
            return None

    mock_client = _make_mock_client()

    with (
        patch("middleware.harvester.orchestrator.PLUGIN_FACTORIES", {"inspire": FailingInitPlugin}),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    assert mock_client.harvest_arcs.call_count == 1
    assert len(report.repository_reports) == len(repos)
    assert report.repository_reports[0].harvested_datasets == 0
    assert report.repository_reports[0].failed_datasets == 1
    assert len(report.repository_reports[0].failed_records) == 1


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

        def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
            async def generator() -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
                yield HarvestedArc(arc_json="arc-json")

            return generator()

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
        patch("middleware.harvester.orchestrator.PLUGIN_FACTORIES", {"inspire": RunnerPlugin}),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    # harvest_arcs was called for both repos; first raised, second succeeded
    assert mock_client.harvest_arcs.call_count == len(repos)
    assert len(report.repository_reports) == len(repos)
    assert report.repository_reports[0].harvest_id is None
    assert report.repository_reports[1].harvest_id == "harvest-1"


@pytest.mark.asyncio
async def test_catastrophic_upload_error_preserves_harvest_id_from_request_url() -> None:
    """When harvest_arcs raises after create, report still carries the harvest id."""
    repos = [_make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    class RunnerPlugin(Plugin):
        def __init__(self, config: object) -> None:
            self._config = config

        def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
            async def generator() -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
                yield HarvestedArc(arc_json="arc-json")

            return generator()

        async def get_expected_datasets(self) -> int | None:
            return None

    request = httpx.Request(
        "POST",
        "https://middleware-test.example/v3/harvests/harvest-967abfe8-27a3-4776-86e6-4bbe17d98ac2/arcs",
    )
    cause = httpx.ConnectError("", request=request)
    error = ApiClientError("Request failed: ", status_code=None)
    error.__cause__ = cause

    mock_client = _make_mock_client()
    mock_client.harvest_arcs.side_effect = error

    with (
        patch("middleware.harvester.orchestrator.PLUGIN_FACTORIES", {"inspire": RunnerPlugin}),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    assert report.repository_reports[0].harvest_id == "harvest-967abfe8-27a3-4776-86e6-4bbe17d98ac2"
    assert len(report.repository_reports[0].failed_records) == 1


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

        def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
            async def generator() -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
                yield HarvesterError("record failed")
                yield HarvestedArc(arc_json="arc-json")

            return generator()

        async def get_expected_datasets(self) -> int | None:
            return None

    mock_client = _make_mock_client()

    # Capture the arc_stream passed to harvest_arcs and drain it
    collected: list[str] = []

    async def capturing_harvest_arcs(*, arcs: AsyncIterable[str], **_kwargs: object) -> MagicMock:
        async for item in arcs:
            collected.append(item)
        result: MagicMock = mock_client.harvest_arcs.return_value  # type: ignore[assignment]
        return result

    mock_client.harvest_arcs.side_effect = capturing_harvest_arcs

    with (
        patch("middleware.harvester.orchestrator.PLUGIN_FACTORIES", {"inspire": HarvesterErrorPlugin}),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    # Only the valid ARC string passes through the filter, not the HarvesterError
    assert collected == ["arc-json"]
    assert mock_client.harvest_arcs.call_count == 1
    assert report.repository_reports[0].harvested_datasets == 1
    assert report.repository_reports[0].failed_datasets == 1


@pytest.mark.asyncio
async def test_skipped_record_items_are_counted_and_not_uploaded() -> None:
    repos = [_make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    class SkippedPlugin(Plugin):
        def __init__(self, config: object) -> None:
            self._config = config

        def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
            async def generator() -> AsyncGenerator[HarvestedArc | HarvesterError | SkippedRecord, None]:
                yield SkippedRecord("Duplicate sitemap entry skipped", "https://example.org/dup")
                yield HarvestedArc(arc_json="arc-json")

            return generator()

        async def get_expected_datasets(self) -> int | None:
            return None

    mock_client = _make_mock_client()
    collected: list[str] = []

    async def capturing_harvest_arcs(*, arcs: AsyncIterable[str], **_kwargs: object) -> MagicMock:
        async for item in arcs:
            collected.append(item)
        result: MagicMock = mock_client.harvest_arcs.return_value  # type: ignore[assignment]
        return result

    mock_client.harvest_arcs.side_effect = capturing_harvest_arcs

    with (
        patch("middleware.harvester.orchestrator.PLUGIN_FACTORIES", {"inspire": SkippedPlugin}),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    assert collected == ["arc-json"]
    assert report.repository_reports[0].harvested_datasets == 1
    assert report.repository_reports[0].failed_datasets == 0
    assert report.repository_reports[0].skipped_datasets == 1


@pytest.mark.asyncio
async def test_run_orchestrator_gathers_repositories_and_uses_expected_datasets() -> None:
    repos = [_make_repo("inspire"), _make_repo("linked_data")]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    mock_client = _make_mock_client()
    expected_datasets = 10
    expected_harvest_calls = 2

    report = await _run_orchestrator_with_test_plugins(mock_config, mock_client, expected_datasets)

    assert mock_client.harvest_arcs.call_count == expected_harvest_calls
    assert all(call.kwargs["expected_datasets"] == expected_datasets for call in mock_client.harvest_arcs.mock_calls)
    assert len(report.repository_reports) == len(repos)
    assert report.repository_reports[0].expected_datasets == expected_datasets


@pytest.mark.asyncio
async def test_run_orchestrator_returns_when_no_repositories() -> None:
    mock_config = MagicMock()
    mock_config.repositories = []
    mock_config.api_client = MagicMock()

    mock_client = _make_mock_client()
    with patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client):
        report = await run_orchestrator(mock_config)

    assert mock_client.harvest_arcs.call_count == 0
    assert report.repository_reports == ()


def test_emit_report_via_shared_counting_api() -> None:
    """Harvester emit path uses finished HarvestReport + JsonLdReportSerializer."""
    report = HarvestReport(start_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
    scope = report.open_repository("bonares")
    scope.set_harvest_id("harvest-1")
    for _ in range(5):
        scope.record_harvested()
    scope.record_failed("boom")
    scope.add_studies(2)
    scope.add_assays(2)
    scope.close()
    report.finish(end_time=datetime(2026, 1, 1, 0, 1, tzinfo=UTC))

    jsonld = json.loads(JsonLdReportSerializer().render(report))["schema:result"][0]

    assert jsonld["@type"] == "schema:EntryPoint"
    assert jsonld["fairagro:harvestId"] == "harvest-1"
    assert "fairagro:expectedDatasets" not in jsonld
    assert jsonld["fairagro:harvestedDatasets"] == 5
    assert jsonld["fairagro:failedDatasets"] == 1
    assert jsonld["fairagro:skippedDatasets"] == 0
    assert jsonld["fairagro:totalStudies"] == 2
    assert jsonld["fairagro:totalAssays"] == 2


def test_emit_report_logs_warning_on_serialisation_failure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    report = HarvestReport(start_time=datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
    report.finish(end_time=datetime(2026, 1, 1, 0, 1, tzinfo=UTC))

    class BrokenSerializer:
        def render(self, _: HarvestReport) -> str:
            raise TypeError("boom")

    monkeypatch.setattr(
        "middleware.harvester.reporting.JsonLdReportSerializer",
        BrokenSerializer,
    )
    emit_report(report)

    assert "Failed to serialise harvest report" in caplog.text


def test_harvested_arc_from_arctrl_uses_object_counts() -> None:

    investigation = ArcInvestigation.create("example", title="Example")
    investigation.AddStudy(ArcStudy("s1"))
    investigation.AddAssay(ArcAssay("a1"))
    arc = ARC.from_arc_investigation(investigation)

    harvested = HarvestedArc.from_arctrl(arc, source_url="https://example.org/r1")
    assert harvested.identifier == "example"
    assert harvested.studies == 1
    assert harvested.assays == 1
    assert harvested.source_url == "https://example.org/r1"
    assert '"@graph"' in harvested.arc_json


@pytest.mark.asyncio
async def test_run_repository_sums_studies_and_assays_from_harvested_arcs() -> None:
    """Successfully harvested ARCs contribute total_studies / total_assays on the report."""
    repos = [_make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    class TwoArcPlugin(Plugin):
        def __init__(self, config: object) -> None:
            self._config = config

        def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
            async def generator() -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
                yield HarvestedArc(arc_json="{}", studies=1, assays=1)
                yield HarvestedArc(arc_json="{}", studies=1, assays=1)

            return generator()

        async def get_expected_datasets(self) -> int | None:
            return 2

    mock_client = _make_mock_client()

    async def capturing_harvest_arcs(*, arcs: AsyncIterable[str], **_kwargs: object) -> MagicMock:
        async for _item in arcs:
            pass
        result: MagicMock = mock_client.harvest_arcs.return_value  # type: ignore[assignment]
        return result

    mock_client.harvest_arcs.side_effect = capturing_harvest_arcs

    with (
        patch("middleware.harvester.orchestrator.PLUGIN_FACTORIES", {"inspire": TwoArcPlugin}),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    entry = report.repository_reports[0]
    assert entry.harvested_datasets == 2
    assert entry.total_studies == 2
    assert entry.total_assays == 2


@pytest.mark.asyncio
async def test_run_repository_unknown_plugin_skips_repo() -> None:
    repo = _make_repo("unknown")
    mock_client = _make_mock_client()
    tracer = MagicMock()
    report = HarvestReport()

    with patch("middleware.harvester.orchestrator.logger") as mock_logger:
        await run_repository(repo, mock_client, tracer, report)

    report.finish()
    assert mock_client.harvest_arcs.call_count == 0
    mock_logger.error.assert_called_once()
    assert len(report.repository_reports) == 1
    entry = report.repository_reports[0]
    assert entry.harvested_datasets == 0
    assert entry.failed_datasets == 1
    assert entry.failed_records[0].message == "Unknown repository type 'unknown'"


@pytest.mark.asyncio
async def test_run_orchestrator_returns_report_when_all_tasks_fail() -> None:
    repos = [_make_repo(), _make_repo()]
    repos[0].rdi = "inspire-rdi-0"
    repos[1].rdi = "inspire-rdi-1"
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    mock_client = _make_mock_client()

    async def failing_run(
        _repo: MagicMock,
        _client: AsyncMock,
        _tracer: MagicMock,
        _report: HarvestReport,
    ) -> None:
        raise RuntimeError("task failed")

    with (
        patch("middleware.harvester.orchestrator.run_repository", failing_run),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    assert len(report.repository_reports) == len(repos)
    assert all(repo.harvest_id is None for repo in report.repository_reports)
    assert all(repo.failed_datasets == 1 for repo in report.repository_reports)


@pytest.mark.asyncio
async def test_gather_escape_does_not_duplicate_repository_scope() -> None:
    """CancelledError after open_repository must keep a single report entry."""
    repos = [_make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()
    mock_client = _make_mock_client()

    class CancellingPlugin(Plugin):
        def __init__(self, config: object) -> None:
            self._config = config

        def run(self) -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
            async def generator() -> AsyncGenerator[HarvestedArc | HarvesterError, None]:
                if False:  # pragma: no cover - required for AsyncGenerator typing
                    yield HarvestedArc(arc_json="{}")
                raise asyncio.CancelledError

            return generator()

        async def get_expected_datasets(self) -> int | None:
            raise asyncio.CancelledError

    with (
        patch("middleware.harvester.orchestrator.PLUGIN_FACTORIES", {"inspire": CancellingPlugin}),
        patch("middleware.harvester.orchestrator.ApiClient", return_value=mock_client),
    ):
        report = await run_orchestrator(mock_config)

    assert len(report.repository_reports) == 1
    assert report.repository_reports[0].failed_datasets == 1
    assert mock_client.harvest_arcs.call_count == 0


def test_main_logs_exception_message_without_traceback_at_info(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    """Prod ERROR logs include the cause; traceback stays on DEBUG only."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("log_level: INFO\nrepositories: []\n")

    with (
        patch("middleware.harvester.main._parse_args", return_value=MagicMock(config=str(config_file))),
        patch(
            "middleware.harvester.main.Config.from_yaml_file",
            side_effect=ConnectionError("CSW endpoint unreachable"),
        ),
        caplog.at_level(logging.INFO),
    ):
        assert main() == 1

    assert "Harvester run failed: ConnectionError" in caplog.text
    assert "CSW endpoint unreachable" in caplog.text
    assert "Traceback" not in caplog.text


def test_main_logs_traceback_at_debug(caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    """DEBUG includes the exception traceback for local diagnosis."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("log_level: DEBUG\nrepositories: []\n")

    with (
        patch("middleware.harvester.main._parse_args", return_value=MagicMock(config=str(config_file))),
        patch(
            "middleware.harvester.main.Config.from_yaml_file",
            side_effect=ConnectionError("CSW endpoint unreachable"),
        ),
        caplog.at_level(logging.DEBUG),
    ):
        assert main() == 1

    assert "Harvester run failed: ConnectionError" in caplog.text
    assert "CSW endpoint unreachable" in caplog.text
    assert "Traceback" in caplog.text
