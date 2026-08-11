"""Unit tests for the INSPIRE CSW client."""

import gc
import logging
import warnings
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from middleware.harvester.errors import RecordProcessingError
from middleware.inspire.config import Config
from middleware.inspire.csw_client import CSWClient
from middleware.inspire.errors import CswConnectionError
from middleware.inspire.models import InspireRecord

_expected_record_count = 42


def _make_csw_config(csw_url: str = "https://example.com/csw") -> Config:
    return Config(csw_url=csw_url, timeout=5, chunk_size=10)


def test_get_record_url_appends_query_parameters() -> None:
    config = _make_csw_config(csw_url="https://example.com/csw?foo=bar")
    client = CSWClient(config)

    url = client.get_record_url("record-123")

    assert "?foo=bar&" in url
    assert "id=record-123" in url


def test_get_record_url_handles_base_url_without_query() -> None:
    config = _make_csw_config(csw_url="https://example.com/csw")
    client = CSWClient(config)

    url = client.get_record_url("record-123")

    assert url.startswith("https://example.com/csw?")
    assert "id=record-123" in url


def test_connect_logs_cs_title_on_success(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    config = _make_csw_config()
    client = CSWClient(config)
    fake_csw = MagicMock()
    fake_csw.identification = MagicMock(title="Test CSW")

    with patch("middleware.inspire.csw_client.CatalogueServiceWeb", return_value=fake_csw):
        client.connect()

    assert object.__getattribute__(client, "_csw") is fake_csw
    assert "Connected to CSW at https://example.com/csw: Test CSW" in caplog.text


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
    config = _make_csw_config()
    client = CSWClient(config)
    fake_csw = MagicMock()

    def getrecords2(**_kwargs: object) -> None:
        fake_csw.results = {"matches": ["7"]}

    fake_csw.getrecords2.side_effect = getrecords2
    object.__setattr__(client, "_csw", fake_csw)

    expected_count = 7
    count = client.get_record_count(xml_query=_minimal_get_records_xml())

    assert count == expected_count


def test_get_record_count_uses_xml_query_with_encoding_declaration() -> None:
    config = _make_csw_config()
    client = CSWClient(config)
    fake_csw = MagicMock()

    def getrecords2(**kwargs: object) -> None:
        assert isinstance(kwargs.get("xml"), bytes)
        fake_csw.results = {"matches": ["11"]}

    fake_csw.getrecords2.side_effect = getrecords2
    object.__setattr__(client, "_csw", fake_csw)

    expected_count = 11
    xml_request = '<?xml version="1.0" encoding="UTF-8"?>' + _minimal_get_records_xml()
    count = client.get_record_count(xml_query=xml_request)

    assert count == expected_count


def test_config_default_csw_thread_pool_size() -> None:
    config = _make_csw_config()

    assert config.csw_thread_pool_size == 4  # noqa: PLR2004


@pytest.mark.asyncio
async def test_csw_client_executor_is_created_and_shutdown_in_context_manager() -> None:
    config = _make_csw_config()
    client = CSWClient(config)

    with patch("middleware.inspire.csw_client.ThreadPoolExecutor") as executor_factory:
        fake_executor = MagicMock()
        executor_factory.return_value = fake_executor

        async with client:
            executor_factory.assert_called_once_with(max_workers=4)

        fake_executor.shutdown.assert_called_once_with(wait=False)


@pytest.mark.asyncio
async def test_csw_client_executor_shutdown_on_del_without_warning() -> None:
    config = _make_csw_config()
    client = CSWClient(config)

    with patch("middleware.inspire.csw_client.ThreadPoolExecutor") as executor_factory:
        fake_executor = MagicMock()
        executor_factory.return_value = fake_executor

        # Build the executor lazily.
        client.get_executor()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        del client
        gc.collect()

    assert len(caught) == 0
    fake_executor.shutdown.assert_called_once_with(wait=False)


def test_connect_raises_csw_connection_error_on_failure() -> None:
    config = _make_csw_config()
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


def test_connect_forwards_default_verify_ssl() -> None:
    config = _make_csw_config()
    client = CSWClient(config)
    fake_csw = MagicMock()

    with patch("middleware.inspire.csw_client.CatalogueServiceWeb", return_value=fake_csw) as mock_factory:
        client.connect()

    auth = mock_factory.call_args.kwargs["auth"]
    assert auth.verify is True


def test_connect_forwards_verify_ssl_false(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    config = Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10, verify_ssl=False)
    client = CSWClient(config)
    fake_csw = MagicMock()

    with patch("middleware.inspire.csw_client.CatalogueServiceWeb", return_value=fake_csw) as mock_factory:
        client.connect()

    auth = mock_factory.call_args.kwargs["auth"]
    assert auth.verify is False
    assert "TLS certificate verification is disabled" in caplog.text


def test_connect_forwards_verify_ssl_ca_path(caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    caplog.set_level(logging.WARNING)
    ca_path = tmp_path / "custom-ca.pem"
    ca_path.write_text("dummy-ca\n", encoding="utf-8")
    config = Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10, verify_ssl=str(ca_path))
    client = CSWClient(config)
    fake_csw = MagicMock()

    with patch("middleware.inspire.csw_client.CatalogueServiceWeb", return_value=fake_csw) as mock_factory:
        client.connect()

    auth = mock_factory.call_args.kwargs["auth"]
    assert auth.verify == str(ca_path)
    assert "TLS certificate verification is disabled" not in caplog.text


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

    def iter_to_list_side_effect(*_args: object, **_kwargs: object) -> list[str]:
        result = side_effect.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    expected_calls = 2

    with patch.object(CSWClient, "_iter_to_list", side_effect=iter_to_list_side_effect) as mock_iter:
        records = [item async for item in client.get_records_async()]

    assert records == ["record1"]
    assert mock_iter.call_count == expected_calls


@pytest.mark.asyncio
async def test_get_records_async_uses_run_in_executor_for_cql_path() -> None:
    config = Config(
        csw_url="https://example.com/csw",
        cql_query="AnyText LIKE '%agriculture%'",
        timeout=5,
        chunk_size=10,
    )
    client = CSWClient(config)
    object.__setattr__(client, "_csw", MagicMock())

    fake_loop = MagicMock()
    fake_loop.run_in_executor = AsyncMock(side_effect=lambda _executor, func, *args, **kwargs: func(*args, **kwargs))

    with (
        patch("middleware.inspire.csw_client.asyncio.get_running_loop", return_value=fake_loop),
        patch.object(CSWClient, "_get_executor", return_value=MagicMock()),
        patch.object(CSWClient, "_connect", return_value=None),
        patch.object(CSWClient, "_get_records_by_cql", return_value=iter(["record1"])) as mock_sync,
    ):
        records = [item async for item in client.get_records_async()]

    assert records == ["record1"]
    mock_sync.assert_called_once_with("AnyText LIKE '%agriculture%'", 10, None)
    assert fake_loop.run_in_executor.called


@pytest.mark.asyncio
async def test_get_records_async_uses_run_in_executor_for_xml_path() -> None:
    config = _make_csw_config()
    client = CSWClient(config)
    object.__setattr__(client, "_csw", MagicMock())

    fake_loop = MagicMock()
    fake_loop.run_in_executor = AsyncMock(side_effect=lambda _executor, func, *args, **kwargs: func(*args, **kwargs))

    with (
        patch("middleware.inspire.csw_client.asyncio.get_running_loop", return_value=fake_loop),
        patch.object(CSWClient, "_get_executor", return_value=MagicMock()),
        patch.object(CSWClient, "_connect", return_value=None),
        patch.object(CSWClient, "_get_records_by_xml_prepared", return_value=iter(["record1"])) as mock_sync,
    ):
        records = [item async for item in client.get_records_async(xml_query=_minimal_get_records_xml())]

    assert records == ["record1"]
    assert mock_sync.called
    assert fake_loop.run_in_executor.called


def test_get_records_uses_fes_constraints() -> None:
    config = _make_csw_config()
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


def test_next_start_position_prefers_nextrecord() -> None:
    client = CSWClient(_make_csw_config())
    csw = MagicMock()
    next_start = 51
    csw.results = {"matches": 113, "returned": 50, "nextrecord": next_start}
    object.__setattr__(client, "_csw", csw)

    assert client._next_start_position(1) == next_start  # noqa: SLF001

    csw.results = {"matches": 113, "returned": 13, "nextrecord": 0}
    assert client._next_start_position(101) is None  # noqa: SLF001


def test_next_start_position_falls_back_to_start_plus_returned() -> None:
    client = CSWClient(_make_csw_config())
    csw = MagicMock()
    csw.results = {"matches": 113, "returned": 50, "nextrecord": None}
    object.__setattr__(client, "_csw", csw)

    assert client._next_start_position(1) == 1 + 50  # noqa: SLF001


def test_next_start_position_falls_back_to_batch_length_when_metadata_missing() -> None:
    """When nextrecord/returned are absent, advance using batch length if matches remain."""
    client = CSWClient(_make_csw_config())
    csw = MagicMock()
    csw.results = {"matches": 113, "returned": None, "nextrecord": None}
    object.__setattr__(client, "_csw", csw)

    batch_size = 50
    assert client._next_start_position(1, records_in_batch=batch_size) == 1 + batch_size  # noqa: SLF001
    assert client._next_start_position(101, records_in_batch=13) is None  # noqa: SLF001


def test_paged_harvest_advances_when_nextrecord_and_returned_missing() -> None:
    """Missing pagination metadata must not truncate the harvest while matches remain."""
    starts: list[int] = []
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=50))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    batch_sizes = [50, 50, 13]

    def fake_fetch(
        batch_size: int,
        start_position: int,
        cql_query: str | None,
        fes_constraints: object,
    ) -> bool:
        del batch_size, cql_query, fes_constraints
        starts.append(start_position)
        csw.results = {"matches": 113, "returned": None, "nextrecord": None}
        return True

    def fake_parse() -> tuple[list[object], list[object], int]:
        page_index = len(starts) - 1
        size = batch_sizes[page_index]
        return ([object()] * size, [], size)

    with (
        patch.object(CSWClient, "_fetch_iso_batch", side_effect=fake_fetch),
        patch.object(CSWClient, "_parse_iso_batch", side_effect=fake_parse),
    ):
        list(client._get_records_paged(50, None, None, None))  # noqa: SLF001

    assert starts == [1, 51, 101]


def test_paged_harvest_starts_at_one_and_advances_without_overlap() -> None:
    """CSW startPosition is 1-based; pages must not request the previous boundary again."""
    page_starts = [1, 51, 101]
    nextrecords = [51, 101, 0]
    last_full_page_index = 1
    starts: list[int] = []
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=50))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)

    def fake_fetch(
        batch_size: int,
        start_position: int,
        cql_query: str | None,
        fes_constraints: object,
    ) -> bool:
        del batch_size, cql_query, fes_constraints
        page_index = len(starts)
        starts.append(start_position)
        csw.results = {
            "matches": 113,
            "returned": 50 if page_index <= last_full_page_index else 13,
            "nextrecord": nextrecords[page_index],
        }
        return True

    with (
        patch.object(CSWClient, "_fetch_iso_batch", side_effect=fake_fetch),
        patch.object(CSWClient, "_parse_iso_batch", return_value=([object()], [], 1)),
    ):
        list(client._get_records_paged(50, None, None, None))  # noqa: SLF001

    assert starts == page_starts


def test_all_records_fetched_allows_start_equal_to_matches() -> None:
    """Position ``matches`` is still valid under 1-based CSW indexing."""
    client = CSWClient(_make_csw_config())
    csw = MagicMock()
    csw.results = {"matches": 151}
    object.__setattr__(client, "_csw", csw)

    assert client._all_records_fetched(151) is False  # noqa: SLF001
    assert client._all_records_fetched(152) is True  # noqa: SLF001


def test_paged_harvest_fetches_final_record_when_nextrecord_equals_matches() -> None:
    """When nextrecord == matches, the last page must still be requested."""
    page_starts = [1, 141, 151]
    nextrecords = [141, 151, 0]
    returned_counts = [140, 10, 1]
    starts: list[int] = []
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=50))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)

    def fake_fetch(
        batch_size: int,
        start_position: int,
        cql_query: str | None,
        fes_constraints: object,
    ) -> bool:
        del batch_size, cql_query, fes_constraints
        page_index = len(starts)
        starts.append(start_position)
        csw.results = {
            "matches": 151,
            "returned": returned_counts[page_index],
            "nextrecord": nextrecords[page_index],
        }
        return True

    with (
        patch.object(CSWClient, "_fetch_iso_batch", side_effect=fake_fetch),
        patch.object(CSWClient, "_parse_iso_batch", return_value=([object()], [], 1)),
    ):
        list(client._get_records_paged(50, None, None, None))  # noqa: SLF001

    assert starts == page_starts


def test_paged_harvest_stops_when_nextrecord_does_not_advance() -> None:
    """A stuck nextrecord must not spin the pagination loop forever."""
    starts: list[int] = []
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=50))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)

    def fake_fetch(
        batch_size: int,
        start_position: int,
        cql_query: str | None,
        fes_constraints: object,
    ) -> bool:
        del batch_size, cql_query, fes_constraints
        starts.append(start_position)
        csw.results = {"matches": 200, "returned": 50, "nextrecord": start_position}
        return True

    with (
        patch.object(CSWClient, "_fetch_iso_batch", side_effect=fake_fetch),
        patch.object(CSWClient, "_parse_iso_batch", return_value=([object()], [], 1)),
    ):
        list(client._get_records_paged(50, None, None, None))  # noqa: SLF001

    assert starts == [1]


def _minimal_get_records_xml(**attrs: str) -> str:
    attr_str = " ".join(f'{key}="{value}"' for key, value in attrs.items())
    return (
        '<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" '
        'service="CSW" version="2.0.2" resultType="results" '
        'outputSchema="http://www.isotc211.org/2005/gmd"'
        f"{(' ' + attr_str) if attr_str else ''}>"
        '<csw:Query typeNames="csw:Record">'
        "<csw:ElementSetName>full</csw:ElementSetName>"
        "</csw:Query>"
        "</csw:GetRecords>"
    )


def test_xml_paging_uses_chunk_size_across_pages() -> None:
    """xml_query without maxRecords uses config chunk_size and pages via nextrecord."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=2))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    sent: list[str] = []
    pages = [
        {"matches": 3, "returned": 2, "nextrecord": 3},
        {"matches": 3, "returned": 1, "nextrecord": 0},
    ]

    def fake_getrecords2(*, xml: str) -> None:
        sent.append(xml)
        page = pages[len(sent) - 1]
        csw.results = page
        csw.records = {}

    csw.getrecords2.side_effect = fake_getrecords2

    with patch.object(CSWClient, "_parse_iso_batch", side_effect=[([object(), object()], [], 2), ([object()], [], 1)]):
        list(client.get_records(xml_query=_minimal_get_records_xml()))

    assert len(sent) == 2
    assert 'maxRecords="2"' in sent[0]
    assert 'startPosition="1"' in sent[0]
    assert 'maxRecords="2"' in sent[1]
    assert 'startPosition="3"' in sent[1]


def test_xml_max_records_overrides_chunk_size() -> None:
    """Valid XML maxRecords overrides config chunk_size as page size only."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=50))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.results = {"matches": 1, "returned": 1, "nextrecord": 0}
    csw.records = {}

    with patch.object(CSWClient, "_parse_iso_batch", return_value=([object()], [], 1)):
        list(client.get_records(xml_query=_minimal_get_records_xml(maxRecords="7")))

    sent_xml = csw.getrecords2.call_args.kwargs["xml"]
    assert 'maxRecords="7"' in sent_xml


def test_xml_start_position_overrides_initial_offset() -> None:
    """Valid XML startPosition is used as the first page offset."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.results = {"matches": 20, "returned": 1, "nextrecord": 0}
    csw.records = {}

    with patch.object(CSWClient, "_parse_iso_batch", return_value=([object()], [], 1)):
        list(client.get_records(xml_query=_minimal_get_records_xml(startPosition="11")))

    sent_xml = csw.getrecords2.call_args.kwargs["xml"]
    assert 'startPosition="11"' in sent_xml


def test_xml_config_max_records_caps_harvest() -> None:
    """Config max_records stops XML harvest across pages (not XML maxRecords)."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=2, max_records=2))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    call_count = 0

    def fake_getrecords2(*, xml: str) -> None:
        del xml
        nonlocal call_count
        call_count += 1
        csw.results = {"matches": 100, "returned": 2, "nextrecord": 3}
        csw.records = {}

    csw.getrecords2.side_effect = fake_getrecords2

    with patch.object(CSWClient, "_parse_iso_batch", return_value=([object(), object()], [], 2)):
        results = list(client.get_records(xml_query=_minimal_get_records_xml()))

    assert len(results) == 2
    assert call_count == 1


def test_xml_invalid_paging_attrs_log_and_fall_back(caplog: pytest.LogCaptureFixture) -> None:
    """Invalid XML maxRecords/startPosition are ignored with a warning."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=9))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.results = {"matches": 1, "returned": 1, "nextrecord": 0}
    csw.records = {}

    with (
        caplog.at_level(logging.WARNING, logger="middleware.inspire.csw_client"),
        patch.object(CSWClient, "_parse_iso_batch", return_value=([object()], [], 1)),
    ):
        list(
            client.get_records(
                xml_query=_minimal_get_records_xml(maxRecords="0", startPosition="bogus"),
            )
        )

    sent_xml = csw.getrecords2.call_args.kwargs["xml"]
    assert 'maxRecords="9"' in sent_xml
    assert 'startPosition="1"' in sent_xml
    assert any("maxRecords" in record.message for record in caplog.records)
    assert any("startPosition" in record.message for record in caplog.records)


def test_xml_query_requires_get_records_root() -> None:
    """xml_query without a GetRecords root raises before contacting CSW."""
    client = CSWClient(_make_csw_config())

    with (
        patch.object(client, "connect") as mock_connect,
        pytest.raises(ValueError, match="GetRecords"),
    ):
        list(client.get_records(xml_query="<Filter/>"))

    mock_connect.assert_not_called()


def test_xml_query_rejects_nested_get_records() -> None:
    """GetRecords must be the document root, not a descendant."""
    client = CSWClient(_make_csw_config())
    wrapped = (
        "<wrapper>"
        '<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" '
        'service="CSW" version="2.0.2"/>'
        "</wrapper>"
    )

    with (
        patch.object(client, "connect") as mock_connect,
        pytest.raises(ValueError, match="GetRecords"),
    ):
        list(client.get_records(xml_query=wrapped))

    mock_connect.assert_not_called()


def test_xml_query_rejects_wrong_get_records_namespace() -> None:
    """GetRecords in a non-CSW namespace is rejected."""
    client = CSWClient(_make_csw_config())

    with (
        patch.object(client, "connect") as mock_connect,
        pytest.raises(ValueError, match="GetRecords"),
    ):
        list(client.get_records(xml_query='<GetRecords xmlns="http://example.org/not-csw"/>'))

    mock_connect.assert_not_called()


def test_xml_query_rejects_unnamespaced_get_records() -> None:
    """Bare GetRecords without the CSW 2.0.2 namespace is rejected."""
    client = CSWClient(_make_csw_config())

    with (
        patch.object(client, "connect") as mock_connect,
        pytest.raises(ValueError, match="GetRecords"),
    ):
        list(client.get_records(xml_query='<GetRecords service="CSW" version="2.0.2"/>'))

    mock_connect.assert_not_called()


def test_max_records_truncates_oversized_page() -> None:
    """max_records must not yield more successful records than N within a page."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=10, max_records=2))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.results = {"matches": 10, "returned": 5, "nextrecord": 6}
    csw.records = {}
    call_count = 0

    def fake_getrecords2(**_kwargs: object) -> None:
        nonlocal call_count
        call_count += 1

    csw.getrecords2.side_effect = fake_getrecords2
    page: tuple[list[object], list[object], int] = (
        [object(), object(), object(), object(), object()],
        [],
        5,
    )

    with patch.object(CSWClient, "_parse_iso_batch", return_value=page):
        results = list(client.get_records(xml_query=_minimal_get_records_xml()))

    assert len(results) == 2
    assert call_count == 1


def _stub_inspire_record(identifier: str) -> InspireRecord:
    """Minimal InspireRecord for limit/pagination unit tests."""
    return InspireRecord.model_construct(identifier=identifier, title=identifier, abstract="")


def test_limit_page_keeps_errors_after_success_budget() -> None:
    """max_records caps successes only; RecordProcessingErrors on the page are still kept."""
    ok1, ok2, ok3 = (_stub_inspire_record(f"ok-{i}") for i in range(1, 4))
    err_mid = RecordProcessingError("mid", record_id="e-mid")
    err_tail = RecordProcessingError("tail", record_id="e-tail")
    page: list[InspireRecord | RecordProcessingError] = [ok1, err_mid, ok2, ok3, err_tail]

    limited, successes = CSWClient._limit_page_to_max_records(  # noqa: SLF001
        page,
        count=3,
        records_yielded=0,
        max_records=2,
    )

    assert successes == 2
    assert limited == [ok1, err_mid, ok2, err_tail]


def test_limit_page_keeps_errors_when_success_budget_already_exhausted() -> None:
    """When remaining <= 0, successes are dropped but page errors are still returned."""
    ok = _stub_inspire_record("ok-1")
    err = RecordProcessingError("still report me", record_id="e-1")
    page: list[InspireRecord | RecordProcessingError] = [ok, err]

    limited, successes = CSWClient._limit_page_to_max_records(  # noqa: SLF001
        page,
        count=1,
        records_yielded=5,
        max_records=5,
    )

    assert successes == 0
    assert limited == [err]


def test_pagination_fallback_uses_fetched_size_not_trimmed_yield() -> None:
    """Missing nextrecord/returned must advance by the fetched page size, not a trimmed yield list."""
    starts: list[int] = []
    batch_sizes_seen: list[int] = []
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=5, max_records=100))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)

    def fake_fetch(
        batch_size: int,
        start_position: int,
        cql_query: str | None,
        fes_constraints: object,
    ) -> bool:
        del batch_size, cql_query, fes_constraints
        starts.append(start_position)
        csw.results = {"matches": 20, "returned": None, "nextrecord": None}
        return True

    def fake_limit(
        results: list[object],
        count: int,
        records_yielded: int,
        max_records: int | None,
    ) -> tuple[list[object], int]:
        del count, records_yielded, max_records
        # Shrink the yield list while leaving budget so pagination continues.
        return results[:2], 2

    real_advance = client._advance_start_position  # noqa: SLF001

    def tracking_advance(start_position: int, records_in_batch: int) -> int | None:
        batch_sizes_seen.append(records_in_batch)
        return real_advance(start_position, records_in_batch=records_in_batch)

    with (
        patch.object(CSWClient, "_fetch_iso_batch", side_effect=fake_fetch),
        patch.object(CSWClient, "_parse_iso_batch", return_value=([object()] * 5, [], 5)),
        patch.object(CSWClient, "_limit_page_to_max_records", side_effect=fake_limit),
        patch.object(client, "_advance_start_position", side_effect=tracking_advance),
    ):
        list(client._get_records_paged(5, None, None, 100))  # noqa: SLF001

    assert batch_sizes_seen[0] == 5
    assert starts[0] == 1
    assert starts[1] == 6


def test_xml_iso_fetch_does_not_mutate_shared_template() -> None:
    """ISO page fetches must not rewrite the shared xml_query root in-place."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=2))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.results = {"matches": 3, "returned": 2, "nextrecord": 3}
    csw.records = {}

    original_schema = "http://www.opengis.net/cat/csw/2.0.2"
    xml_query = (
        '<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" '
        'service="CSW" version="2.0.2" resultType="results" '
        f'outputSchema="{original_schema}" startPosition="9" maxRecords="99">'
        '<csw:Query typeNames="csw:Record">'
        "<csw:ElementSetName>full</csw:ElementSetName>"
        "</csw:Query>"
        "</csw:GetRecords>"
    )
    root, page_size, start, as_bytes = client._prepare_xml_paging(xml_query, chunk_size=2)  # noqa: SLF001
    assert page_size == 99
    assert start == 9

    client._fetch_iso_batch_xml(root, batch_size=2, start_position=1, as_bytes=as_bytes)  # noqa: SLF001
    client._fetch_iso_batch_xml(root, batch_size=2, start_position=3, as_bytes=as_bytes)  # noqa: SLF001

    assert root.get("outputSchema") == original_schema
    assert root.get("startPosition") == "9"
    assert root.get("maxRecords") == "99"
    sent = csw.getrecords2.call_args_list[-1].kwargs["xml"]
    assert 'outputSchema="http://www.isotc211.org/2005/gmd"' in sent
    assert 'startPosition="3"' in sent


def test_xml_non_iso_output_schema_overridden(caplog: pytest.LogCaptureFixture) -> None:
    """ISO fetch path forces gmd outputSchema even when xml_query sets another schema."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=5))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.results = {"matches": 1, "returned": 1, "nextrecord": 0}
    csw.records = {}
    xml_query = (
        '<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" '
        'service="CSW" version="2.0.2" resultType="results" '
        'outputSchema="http://www.opengis.net/cat/csw/2.0.2">'
        '<csw:Query typeNames="csw:Record">'
        "<csw:ElementSetName>full</csw:ElementSetName>"
        "</csw:Query>"
        "</csw:GetRecords>"
    )

    with (
        caplog.at_level(logging.WARNING, logger="middleware.inspire.csw_client"),
        patch.object(CSWClient, "_parse_iso_batch", return_value=([object()], [], 1)),
    ):
        list(client.get_records(xml_query=xml_query))

    sent_xml = csw.getrecords2.call_args.kwargs["xml"]
    assert 'outputSchema="http://www.isotc211.org/2005/gmd"' in sent_xml
    assert any("outputSchema" in record.message for record in caplog.records)


def test_fetch_iso_batch_raises_csw_connection_error_on_failure() -> None:
    """ISO fetch failures raise CswConnectionError so async retry can observe them."""
    client = CSWClient(_make_csw_config())
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.getrecords2.side_effect = TimeoutError("timed out")

    with pytest.raises(CswConnectionError, match="Failed to fetch ISO records"):
        client._fetch_iso_batch(10, 1, None, None)  # noqa: SLF001


def test_fetch_iso_batch_propagates_value_error() -> None:
    """ValueError from OWSLib must propagate unwrapped (not retryable)."""
    client = CSWClient(_make_csw_config())
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.getrecords2.side_effect = ValueError("bad filter")

    with pytest.raises(ValueError, match="bad filter"):
        client._fetch_iso_batch(10, 1, None, None)  # noqa: SLF001


def test_paged_harvest_raises_on_iso_fetch_failure() -> None:
    """A mid-harvest ISO fetch failure raises CswConnectionError (retryable on async path)."""
    client = CSWClient(Config(csw_url="https://example.com/csw", timeout=5, chunk_size=2))
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    call_count = 0

    def fake_getrecords2(**_kwargs: object) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            csw.results = {"matches": 100, "returned": 2, "nextrecord": 3}
            csw.records = {}
            return
        raise TimeoutError("page 2 failed")

    csw.getrecords2.side_effect = fake_getrecords2

    with (
        patch.object(CSWClient, "_parse_iso_batch", return_value=([object(), object()], [], 2)),
        pytest.raises(CswConnectionError, match="Failed to fetch ISO records"),
    ):
        list(client.get_records())

    assert call_count == 2


def test_fetch_iso_batch_xml_raises_csw_connection_error_on_failure() -> None:
    """XML ISO fetch failures raise CswConnectionError on network error."""
    client = CSWClient(_make_csw_config())
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.getrecords2.side_effect = OSError("boom")
    root, _page_size, _start, as_bytes = client._prepare_xml_paging(  # noqa: SLF001
        _minimal_get_records_xml(),
        chunk_size=10,
    )

    with pytest.raises(CswConnectionError, match="Failed to fetch ISO records"):
        client._fetch_iso_batch_xml(root, batch_size=10, start_position=1, as_bytes=as_bytes)  # noqa: SLF001


def test_fetch_iso_batch_xml_propagates_value_error() -> None:
    """ValueError from XML ISO fetch must propagate unwrapped (not retryable)."""
    client = CSWClient(_make_csw_config())
    csw = MagicMock()
    object.__setattr__(client, "_csw", csw)
    csw.getrecords2.side_effect = ValueError("bad xml request")
    root, _page_size, _start, as_bytes = client._prepare_xml_paging(  # noqa: SLF001
        _minimal_get_records_xml(),
        chunk_size=10,
    )

    with pytest.raises(ValueError, match="bad xml request"):
        client._fetch_iso_batch_xml(root, batch_size=10, start_position=1, as_bytes=as_bytes)  # noqa: SLF001
