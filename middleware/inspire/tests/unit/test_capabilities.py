"""Tests for the CSW GetCapabilities readers.

Every reader runs inside ``CSWClient._connect``, so the contract under test is as much
"never raises on a hostile capabilities document" as it is "reports the right number".
"""

import logging
from types import SimpleNamespace

import pytest

from middleware.inspire.capabilities import (
    PageSizeClamp,
    advertised_max_records,
    clamp_page_size,
    describe_service,
    log_page_size_clamp,
    note_server_caps_page_size,
)


def _csw(max_record_default: object = None, *, with_constraints: bool = True) -> SimpleNamespace:
    """Build a stand-in for CatalogueServiceWeb carrying one MaxRecordDefault constraint.

    Mirrors OWSLib's shape: ``constraints`` is a dict of name -> object with ``.values``
    holding a list of strings.
    """
    if not with_constraints:
        return SimpleNamespace()
    constraints: dict[str, object] = {}
    if max_record_default is not None:
        constraints["MaxRecordDefault"] = SimpleNamespace(values=max_record_default)
    return SimpleNamespace(constraints=constraints)


# --- advertised_max_records -----------------------------------------------------------


def test_reads_the_owslib_list_of_strings_shape() -> None:
    """The real shape from OWSLib is a single-element list of strings."""
    assert advertised_max_records(_csw(["10"])) == 10


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param([], id="empty-list"),
        pytest.param(["not-a-number"], id="non-numeric"),
        pytest.param(["0"], id="zero"),
        pytest.param(["-5"], id="negative"),
        pytest.param([None], id="none-inside-list"),
        pytest.param("", id="empty-string"),
        pytest.param(True, id="bool-is-not-a-count"),
    ],
)
def test_returns_none_for_values_that_are_not_a_positive_count(raw: object) -> None:
    """Junk degrades to None rather than raising or yielding a nonsense cap."""
    assert advertised_max_records(_csw(raw)) is None


def test_returns_none_when_the_constraint_is_absent() -> None:
    """Most servers advertise no MaxRecordDefault at all."""
    assert advertised_max_records(_csw()) is None


def test_returns_none_when_constraints_is_missing_entirely() -> None:
    """A reshaped OWSLib response must not raise during connect."""
    assert advertised_max_records(_csw(with_constraints=False)) is None


def test_returns_none_when_constraints_is_not_a_mapping() -> None:
    """Guard the dict assumption explicitly."""
    assert advertised_max_records(SimpleNamespace(constraints=["MaxRecordDefault"])) is None


# --- clamp_page_size ------------------------------------------------------------------


def test_clamp_page_size_reduces_when_advert_is_lower() -> None:
    """Thünen-style advert below the requested page size."""
    assert clamp_page_size(50, 10) == 10


@pytest.mark.parametrize(
    ("page_size", "advertised"),
    [
        pytest.param(50, 100, id="advert-higher"),
        pytest.param(50, 50, id="advert-equal"),
        pytest.param(50, None, id="advert-unknown"),
    ],
)
def test_clamp_page_size_leaves_page_size_when_advert_does_not_bind(page_size: int, advertised: int | None) -> None:
    """Never raise the request size; stay put when the advert is absent or not lower."""
    assert clamp_page_size(page_size, advertised) == page_size


# --- PageSizeClamp / note_server_caps_page_size / log ---------------------------------


def test_from_csw_reads_advert_without_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Connect must not INFO solely because config chunk_size exceeds the advert."""
    with caplog.at_level(logging.INFO):
        clamp = PageSizeClamp.from_csw(_csw(["10"]))

    assert clamp.advertised == 10
    assert caplog.records == []


def test_apply_logs_once_when_page_size_shrinks(caplog: pytest.LogCaptureFixture) -> None:
    """The observed atlas.thuenen.de case: advertises 10, request asks for 50."""
    clamp = PageSizeClamp.from_csw(_csw(["10"]))
    with caplog.at_level(logging.INFO):
        assert clamp.apply(50) == 10
        assert clamp.apply(50) == 10

    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.INFO
    message = caplog.records[0].getMessage()
    assert "MaxRecordDefault" in message
    assert "clamping" in message
    assert "10" in message
    assert "50" in message


def test_apply_stays_silent_when_page_size_already_at_or_below_advert(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """XML maxRecords below the advert must not produce a clamp log."""
    clamp = PageSizeClamp(advertised=10)
    with caplog.at_level(logging.INFO):
        assert clamp.apply(7) == 7

    assert caplog.records == []


@pytest.mark.parametrize(
    ("advertised", "page_size"),
    [
        pytest.param("100", 50, id="cap-above-page-size"),
        pytest.param("50", 50, id="cap-equals-page-size"),
    ],
)
def test_apply_stays_silent_when_the_cap_does_not_bind(
    caplog: pytest.LogCaptureFixture, advertised: str, page_size: int
) -> None:
    """A cap at or above the request page size costs us nothing, so say nothing."""
    clamp = PageSizeClamp(advertised=int(advertised))
    with caplog.at_level(logging.INFO):
        assert clamp.apply(page_size) == page_size

    assert caplog.records == []


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(None, id="constraint-absent"),
        pytest.param(["junk"], id="non-numeric"),
        pytest.param(["0"], id="non-positive"),
    ],
)
def test_stays_silent_when_the_cap_is_unknowable(caplog: pytest.LogCaptureFixture, raw: object) -> None:
    """We only clamp/log about a cap we actually read; otherwise there is nothing to report."""
    with caplog.at_level(logging.INFO):
        assert note_server_caps_page_size(_csw(raw)) is None
        assert PageSizeClamp.from_csw(_csw(raw)).apply(50) == 50

    assert caplog.records == []


def test_does_not_raise_when_the_capabilities_shape_is_unexpected(caplog: pytest.LogCaptureFixture) -> None:
    """Connect must survive a server or OWSLib version we did not anticipate."""
    with caplog.at_level(logging.INFO):
        assert note_server_caps_page_size(SimpleNamespace()) is None
        assert note_server_caps_page_size(object()) is None

    assert caplog.records == []


def test_log_page_size_clamp_is_info_not_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Operators should not see WARNING spam for an intentional clamp."""
    with caplog.at_level(logging.INFO):
        log_page_size_clamp(requested=50, advertised=10)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.INFO


# --- describe_service -----------------------------------------------------------------


def test_returns_the_advertised_title() -> None:
    """The happy path used in the connect log line."""
    csw = SimpleNamespace(identification=SimpleNamespace(title="Thünen Atlas"))
    assert describe_service(csw) == "Thünen Atlas"


@pytest.mark.parametrize(
    "csw",
    [
        pytest.param(SimpleNamespace(identification=None), id="identification-none"),
        pytest.param(SimpleNamespace(), id="identification-absent"),
        pytest.param(SimpleNamespace(identification=SimpleNamespace(title=None)), id="title-none"),
        pytest.param(SimpleNamespace(identification=SimpleNamespace(title=42)), id="title-not-a-string"),
    ],
)
def test_returns_none_when_no_usable_title_is_advertised(csw: object) -> None:
    """Preserves the old behaviour: log None rather than crash or print a repr."""
    assert describe_service(csw) is None
