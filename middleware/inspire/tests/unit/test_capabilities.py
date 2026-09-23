"""Tests for the CSW GetCapabilities readers.

Every reader runs inside ``CSWClient._connect``, so the contract under test is as much
"never raises on a hostile capabilities document" as it is "reports the right number".
"""

import logging
from types import SimpleNamespace

import pytest

from middleware.inspire.capabilities import (
    advertised_max_records,
    describe_service,
    warn_if_server_caps_page_size,
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


# --- warn_if_server_caps_page_size ----------------------------------------------------


def test_warns_when_the_advertised_cap_is_below_chunk_size(caplog: pytest.LogCaptureFixture) -> None:
    """The observed atlas.thuenen.de case: advertises 10, configured 50."""
    with caplog.at_level(logging.WARNING):
        warn_if_server_caps_page_size(_csw(["10"]), chunk_size=50)

    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert "MaxRecordDefault" in message
    # Both numbers must appear, so the line is actionable without re-reading the code.
    assert "10" in message
    assert "50" in message


@pytest.mark.parametrize(
    ("advertised", "chunk_size"),
    [
        pytest.param("100", 50, id="cap-above-chunk-size"),
        pytest.param("50", 50, id="cap-equals-chunk-size"),
    ],
)
def test_stays_silent_when_the_cap_does_not_bind(
    caplog: pytest.LogCaptureFixture, advertised: str, chunk_size: int
) -> None:
    """A cap at or above the configured page size costs us nothing, so say nothing."""
    with caplog.at_level(logging.WARNING):
        warn_if_server_caps_page_size(_csw([advertised]), chunk_size=chunk_size)

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
    """We only warn about a cap we actually read; otherwise there is nothing to report."""
    with caplog.at_level(logging.WARNING):
        warn_if_server_caps_page_size(_csw(raw), chunk_size=50)

    assert caplog.records == []


def test_does_not_raise_when_the_capabilities_shape_is_unexpected(caplog: pytest.LogCaptureFixture) -> None:
    """Connect must survive a server or OWSLib version we did not anticipate."""
    with caplog.at_level(logging.WARNING):
        warn_if_server_caps_page_size(SimpleNamespace(), chunk_size=50)
        warn_if_server_caps_page_size(object(), chunk_size=50)

    assert caplog.records == []


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
