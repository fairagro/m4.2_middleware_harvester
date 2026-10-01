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


def test_max_records_has_no_arbitrary_ceiling() -> None:
    """Operators choose the cap; the config imposes no hardcoded upper bound."""
    config = Config(csw_url="https://example.com/csw", max_records=5_000_000)
    assert config.max_records == 5_000_000


def test_max_records_none_stays_unbounded() -> None:
    """The documented 'harvest everything' default must remain unaffected."""
    config = Config(csw_url="https://example.com/csw")
    assert config.max_records is None


def test_value_bounds_defaults() -> None:
    bounds = Config(csw_url="https://example.com/csw").value_bounds
    assert bounds.max_str_short == 200
    assert bounds.max_str_medium == 1_000
    assert bounds.max_str_long == 10_000
    assert bounds.max_list_items == 500
    assert bounds.allowed_url_schemes == {"http", "https", "ftp"}


def test_value_bounds_can_be_overridden_from_config_mapping() -> None:
    """YAML-shaped input: a list of schemes, mixed case, is normalised to a lowercase set."""
    config = Config.model_validate({
        "csw_url": "https://example.com/csw",
        "value_bounds": {"max_list_items": 10, "allowed_url_schemes": ["HTTPS"]},
    })
    assert config.value_bounds.max_list_items == 10
    assert config.value_bounds.allowed_url_schemes == {"https"}
    assert config.value_bounds.max_str_medium == 1_000  # untouched fields keep defaults


@pytest.mark.parametrize(
    "value_bounds",
    [{"max_str_short": 0}, {"max_list_items": -1}, {"allowed_url_schemes": []}],
)
def test_value_bounds_rejects_nonsensical_limits(value_bounds: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Config.model_validate({"csw_url": "https://example.com/csw", "value_bounds": value_bounds})
