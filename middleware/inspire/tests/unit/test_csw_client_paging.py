"""Unit tests for INSPIRE CSW paging, XML GetRecords, and ISO fetch."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from csw_client_helpers import _make_csw_config, _minimal_get_records_xml, _stub_inspire_record

from middleware.harvester.errors import RecordProcessingError
from middleware.inspire.config import Config
from middleware.inspire.csw_client import CSWClient
from middleware.inspire.errors import CswConnectionError
from middleware.inspire.models import InspireRecord


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
