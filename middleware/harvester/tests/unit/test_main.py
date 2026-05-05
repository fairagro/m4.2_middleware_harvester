"""Unit tests for the Harvester orchestrator main module."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from middleware.harvester.errors import HarvesterError
from middleware.harvester.main import _run_repository, run_orchestrator


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

    def runner(_config: object) -> AsyncGenerator[str, None]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("CSW endpoint unreachable")

        async def _gen() -> AsyncGenerator[str, None]:
            yield "arc-json"

        return _gen()

    mock_client = _make_mock_client()

    with (
        patch("middleware.harvester.main._PLUGIN_RUNNERS", {"inspire": runner}),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
        patch("middleware.harvester.main._get_expected_datasets", return_value=None),
    ):
        await run_orchestrator(mock_config)

    assert mock_client.harvest_arcs.call_count == 1


@pytest.mark.asyncio
async def test_plugin_iteration_exception_skips_repo_and_continues() -> None:
    """If harvest_arcs raises (e.g. generator error propagated), that repo is skipped and the next is processed."""
    repos = [_make_repo(), _make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    def runner(_config: object) -> AsyncGenerator[str, None]:
        async def _gen() -> AsyncGenerator[str, None]:
            yield "arc-json"

        return _gen()

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
        patch("middleware.harvester.main._PLUGIN_RUNNERS", {"inspire": runner}),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
        patch("middleware.harvester.main._get_expected_datasets", return_value=None),
    ):
        await run_orchestrator(mock_config)

    # harvest_arcs was called for both repos; first raised, second succeeded
    assert mock_client.harvest_arcs.call_count == len(repos)


@pytest.mark.asyncio
async def test_harvester_error_yields_logged_and_skipped() -> None:
    """HarvesterError items yielded by the generator are logged and skipped, not uploaded."""
    repos = [_make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    async def runner(_config: object) -> AsyncGenerator[str | HarvesterError, None]:
        yield HarvesterError("record failed")
        yield "arc-json"

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
        patch("middleware.harvester.main._PLUGIN_RUNNERS", {"inspire": runner}),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
        patch("middleware.harvester.main._get_expected_datasets", return_value=None),
    ):
        await run_orchestrator(mock_config)

    # Only the valid ARC string passes through the filter, not the HarvesterError
    assert collected == ["arc-json"]
    assert mock_client.harvest_arcs.call_count == 1


@pytest.mark.asyncio
async def test_run_orchestrator_gathers_repositories_and_uses_expected_datasets() -> None:
    repos = [_make_repo("inspire"), _make_repo("schema_org")]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    async def success_runner(_config: object) -> AsyncGenerator[str, None]:
        yield "arc-json"

    async def failing_runner(_config: object) -> AsyncGenerator[str, None]:
        raise RuntimeError("harvest failure")
        yield  # pragma: no cover

    mock_client = _make_mock_client()
    expected_datasets = 10
    expected_harvest_calls = 2
    mock_get_expected = AsyncMock(return_value=expected_datasets)

    with (
        patch("middleware.harvester.main._PLUGIN_RUNNERS", {"inspire": success_runner, "schema_org": failing_runner}),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
        patch("middleware.harvester.main._get_expected_datasets", mock_get_expected),
    ):
        await run_orchestrator(mock_config)

    assert mock_get_expected.called
    assert mock_client.harvest_arcs.call_count == expected_harvest_calls
    assert all(call.kwargs["expected_datasets"] == expected_datasets for call in mock_client.harvest_arcs.mock_calls)


@pytest.mark.asyncio
async def test_run_orchestrator_returns_when_no_repositories() -> None:
    mock_config = MagicMock()
    mock_config.repositories = []
    mock_config.api_client = MagicMock()

    mock_client = _make_mock_client()
    with patch("middleware.harvester.main.ApiClient", return_value=mock_client):
        await run_orchestrator(mock_config)

    assert mock_client.harvest_arcs.call_count == 0


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
async def test_run_orchestrator_raises_when_all_tasks_fail() -> None:
    repos = [_make_repo(), _make_repo()]
    mock_config = MagicMock()
    mock_config.repositories = repos
    mock_config.api_client = MagicMock()

    mock_client = _make_mock_client()

    async def failing_run(_repo: MagicMock, _client: AsyncMock, _tracer: MagicMock) -> None:
        raise RuntimeError("task failed")

    with (
        patch("middleware.harvester.main._run_repository", failing_run),
        patch("middleware.harvester.main.ApiClient", return_value=mock_client),
        pytest.raises(RuntimeError, match="All repository tasks failed"),
    ):
        await run_orchestrator(mock_config)
