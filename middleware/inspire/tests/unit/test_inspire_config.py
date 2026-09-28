"""Unit tests for `middleware.inspire.config.Config`'s validation constraints.

Named `test_inspire_config.py` (not `test_config.py`) to avoid a module-name collision
with `middleware/linked_data/tests/unit/test_config.py`: both `inspire/tests/unit` and
`linked_data/tests/unit` are on the shared root `pythonpath` (for cross-file test-helper
imports), so a bare `test_config` basename is ambiguous between them at collection time.

These guard `openspec/specs/inspire-value-bounds/`'s config-level requirements.
"""

import pytest
from pydantic import ValidationError

from middleware.inspire.config import Config


@pytest.mark.parametrize(
    "csw_url",
    [
        "javascript:alert(1)",
        "ftp://example.com/csw",
        "file:///etc/passwd",
        "not-a-url",
        "//example.com/csw",  # protocol-relative
    ],
)
def test_csw_url_rejects_non_http_schemes(csw_url: str) -> None:
    with pytest.raises(ValidationError, match="csw_url must be an http"):
        Config(csw_url=csw_url)


@pytest.mark.parametrize("csw_url", ["http://example.com/csw", "https://example.com/csw?service=CSW"])
def test_csw_url_accepts_http_and_https(csw_url: str) -> None:
    config = Config(csw_url=csw_url)
    assert config.csw_url == csw_url


def test_max_records_rejects_value_over_ceiling() -> None:
    with pytest.raises(ValidationError):
        Config(csw_url="https://example.com/csw", max_records=2_000_000)


def test_max_records_accepts_value_under_ceiling() -> None:
    config = Config(csw_url="https://example.com/csw", max_records=500_000)
    assert config.max_records == 500_000


def test_max_records_none_stays_unbounded() -> None:
    """The documented 'harvest everything' default must remain unaffected by the ceiling."""
    config = Config(csw_url="https://example.com/csw")
    assert config.max_records is None
