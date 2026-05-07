"""Unit tests for the INSPIRE CSW client."""

import logging
from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from middleware.inspire.config import Config
from middleware.inspire.csw_client import CSWClient
from middleware.inspire.errors import CswConnectionError

_expected_record_count = 42


def _make_config(csw_url: str = "https://example.com/csw") -> Config:
    return Config(csw_url=csw_url, timeout=5, chunk_size=10)


@pytest.mark.asyncio
async def test_get_records_async_uses_xml_sync_wrapper() -> None:
    config = _make_config()
    client = CSWClient(config)
    object.__setattr__(client, "_csw", MagicMock())

    with patch.object(CSWClient, "_get_records_by_xml_sync", return_value=["record1"]) as mock_xml_sync:
        records = [item async for item in client.get_records_async(xml_query="<xml/>")]

    assert records == ["record1"]
    mock_xml_sync.assert_called_once_with("<xml/>")


def test_get_record_url_appends_query_parameters() -> None:
    config = _make_config(csw_url="https://example.com/csw?foo=bar")
    client = CSWClient(config)

    url = client.get_record_url("record-123")

    assert "?foo=bar&" in url
    assert "id=record-123" in url


def test_get_record_url_handles_base_url_without_query() -> None:
    config = _make_config(csw_url="https://example.com/csw")
    client = CSWClient(config)

    url = client.get_record_url("record-123")

    assert url.startswith("https://example.com/csw?")
    assert "id=record-123" in url


def test_connect_logs_cs_title_on_success(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    config = _make_config()
    client = CSWClient(config)
    fake_csw = MagicMock()
    fake_csw.identification = MagicMock(title="Test CSW")

    with patch("middleware.inspire.csw_client.CatalogueServiceWeb", return_value=fake_csw):
        client.connect()

    assert object.__getattribute__(client, "_csw") is fake_csw
    assert "Connected to CSW: Test CSW" in caplog.text


def test_get_record_count_parses_list_matches() -> None:
    config = Config(
        csw_url="https://example.com/csw",
        cql_query="AnyText LIKE '%agriculture%'",
        timeout=5,
        chunk_size=10,
    )
    client = CSWClient(config)
    fake_csw = MagicMock()

    def getrecords2(**_kwargs: object) -> None:
        fake_csw.results = {"matches": [str(_expected_record_count)]}

    fake_csw.getrecords2.side_effect = getrecords2
    object.__setattr__(client, "_csw", fake_csw)

    count = client.get_record_count()

    assert count == _expected_record_count


def test_get_record_count_uses_xml_query() -> None:
    config = _make_config()
    client = CSWClient(config)
    fake_csw = MagicMock()

    def getrecords2(**_kwargs: object) -> None:
        fake_csw.results = {"matches": ["7"]}

    fake_csw.getrecords2.side_effect = getrecords2
    object.__setattr__(client, "_csw", fake_csw)

    expected_count = 7
    count = client.get_record_count(xml_query="<xml />")

    assert count == expected_count


def test_connect_raises_csw_connection_error_on_failure() -> None:
    config = _make_config()
    client = CSWClient(config)

    with (
        patch("middleware.inspire.csw_client.CatalogueServiceWeb", side_effect=OSError("connection failed")),
        pytest.raises(CswConnectionError, match="Failed to connect to CSW"),
    ):
        client.connect()


def test_connect_forwards_user_agent_header() -> None:
    config = Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10, user_agent="MyAgent")
    client = CSWClient(config)
    fake_csw = MagicMock()

    with patch("middleware.inspire.csw_client.CatalogueServiceWeb", return_value=fake_csw) as mock_factory:
        client.connect()

    assert mock_factory.call_args.kwargs["headers"] == {"User-Agent": "MyAgent"}


@pytest.mark.asyncio
async def test_get_record_count_async_retries_on_oserror() -> None:
    config = Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10, retry_attempts=1)
    client = CSWClient(config)

    expected_count = 7
    expected_calls = 2
    side_effect: list[OSError | int] = [OSError("temporary"), expected_count]

    def get_record_count_side_effect(*_args: object, **_kwargs: object) -> int:
        result = side_effect.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    with patch.object(CSWClient, "get_record_count", side_effect=get_record_count_side_effect) as mock_count:
        result = await client.get_record_count_async()

    assert result == expected_count
    assert mock_count.call_count == expected_calls


@pytest.mark.asyncio
async def test_get_record_count_async_does_not_retry_value_error() -> None:
    config = Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10, retry_attempts=2)
    client = CSWClient(config)

    with (
        patch.object(CSWClient, "get_record_count", side_effect=ValueError("bad query")) as mock_count,
        pytest.raises(
            ValueError,
            match="bad query",
        ),
    ):
        await client.get_record_count_async()

    assert mock_count.call_count == 1


@pytest.mark.asyncio
async def test_get_record_count_async_does_not_retry_http_404() -> None:
    """HTTP 4xx errors must not be retried even though requests.exceptions.HTTPError is an OSError subclass."""
    config = Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10, retry_attempts=3)
    client = CSWClient(config)

    fake_response = MagicMock()
    fake_response.status_code = 404
    http_error = OSError("404 Client Error: Not Found")
    http_error.response = fake_response  # type: ignore[attr-defined]

    with (
        patch.object(CSWClient, "get_record_count", side_effect=http_error) as mock_count,
        pytest.raises(OSError, match="404 Client Error"),
    ):
        await client.get_record_count_async()

    assert mock_count.call_count == 1


@pytest.mark.asyncio
async def test_get_record_count_async_retries_http_503() -> None:
    """HTTP 5xx errors are OSErrors without a 4xx status code, so they should be retried."""
    config = Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10, retry_attempts=1)
    client = CSWClient(config)

    fake_response = MagicMock()
    fake_response.status_code = 503
    http_error = OSError("503 Server Error: Service Unavailable")
    http_error.response = fake_response  # type: ignore[attr-defined]

    expected_count = 42
    expected_calls = 2
    side_effect: list[OSError | int] = [http_error, expected_count]

    def get_record_count_side_effect(*_args: object, **_kwargs: object) -> int:
        result = side_effect.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    with patch.object(CSWClient, "get_record_count", side_effect=get_record_count_side_effect) as mock_count:
        result = await client.get_record_count_async()

    assert result == expected_count
    assert mock_count.call_count == expected_calls


@pytest.mark.asyncio
async def test_get_records_async_retries_on_oserror_in_cql_path() -> None:
    config = Config(
        csw_url="https://example.com/csw",
        cql_query="AnyText LIKE '%agriculture%'",
        timeout=5,
        chunk_size=10,
        retry_attempts=1,
    )
    client = CSWClient(config)
    object.__setattr__(client, "_csw", MagicMock())
    side_effect: list[OSError | list[str]] = [OSError("transient"), ["record1"]]

    def records_side_effect(*_args: object, **_kwargs: object) -> list[str]:
        result = side_effect.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    expected_calls = 2

    with patch.object(CSWClient, "_get_records_by_cql_sync", side_effect=records_side_effect) as mock_sync:
        records = [item async for item in client.get_records_async()]

    assert records == ["record1"]
    assert mock_sync.call_count == expected_calls


@pytest.mark.asyncio
async def test_get_records_async_uses_cql_path() -> None:
    config = Config(
        csw_url="https://example.com/csw",
        cql_query="AnyText LIKE '%agriculture%'",
        timeout=5,
        chunk_size=10,
    )
    client = CSWClient(config)
    object.__setattr__(client, "_csw", MagicMock())

    async def sync_side_effect(func: Callable[..., list[str]], *args: object, **kwargs: object) -> list[str]:
        return func(*args, **kwargs)

    with (
        patch(
            "middleware.inspire.csw_client.asyncio.to_thread",
            new=AsyncMock(side_effect=sync_side_effect),
        ) as mock_to_thread,
        patch.object(CSWClient, "_get_records_by_cql_sync", return_value=["record1"]) as mock_sync,
    ):
        records = [item async for item in client.get_records_async()]

    assert records == ["record1"]
    mock_sync.assert_called_once_with("AnyText LIKE '%agriculture%'", 10, None)
    assert mock_to_thread.called


@pytest.mark.asyncio
async def test_get_records_async_uses_xml_path() -> None:
    config = _make_config()
    client = CSWClient(config)
    object.__setattr__(client, "_csw", MagicMock())

    async def sync_side_effect(func: Callable[..., list[str]], *args: object, **kwargs: object) -> list[str]:
        return func(*args, **kwargs)

    with (
        patch(
            "middleware.inspire.csw_client.asyncio.to_thread",
            new=AsyncMock(side_effect=sync_side_effect),
        ) as mock_to_thread,
        patch.object(CSWClient, "_get_records_by_xml_sync", return_value=["record1"]) as mock_sync,
    ):
        records = [item async for item in client.get_records_async(xml_query="<xml/>")]

    assert records == ["record1"]
    assert mock_sync.called
    assert mock_to_thread.called


def test_get_records_uses_fes_constraints() -> None:
    config = _make_config()
    client = CSWClient(config)
    object.__setattr__(client, "_csw", MagicMock())

    with patch.object(CSWClient, "_get_records_by_fes", return_value=iter(["record1"])) as mock_fes:
        records = list(client.get_records(fes_constraints=[MagicMock()], chunk_size=5, max_records=1))

    assert records == ["record1"]
    mock_fes.assert_called_once()


def test_get_record_count_raises_when_both_filters_are_configured() -> None:
    config = Config.model_construct(
        csw_url="https://example.com/csw",
        cql_query="AnyText LIKE '%agriculture%'",
        xml_query=b"<Filter />",
        chunk_size=1,
        timeout=5,
    )
    client = CSWClient(config)

    with pytest.raises(ValueError, match="Conflicting query parameters"):
        client.get_record_count()
