"""Unit tests for OAI-PMH config and Scythe client helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from middleware.oai_pmh.client import (
    RateLimiter,
    build_http_config,
    build_retry_config,
    check_robots_allowed,
    create_scythe,
)
from middleware.oai_pmh.config import Config
from middleware.oai_pmh.errors import OaiPmhRobotsDisallowedError


def _config(**overrides: object) -> Config:
    raw: dict[str, object] = {
        "endpoint_url": "https://example.org/oai",
        "metadata_prefix": "rdf",
    }
    raw.update(overrides)
    return Config.model_validate(raw)


def test_config_requires_metadata_prefix() -> None:
    with pytest.raises(ValidationError):
        Config.model_validate({"endpoint_url": "https://example.org/oai"})


def test_config_defaults_empty_sets() -> None:
    cfg = _config()
    assert cfg.sets == []
    assert cfg.respect_robots_txt is True


def test_build_http_and_retry_configs() -> None:
    cfg = _config(user_agent="TestAgent/1", timeout=12.5, max_retries=3)
    http = build_http_config(cfg)
    retry = build_retry_config(cfg)
    assert http.user_agent == "TestAgent/1"
    assert http.timeout == 12.5
    assert retry.max_retries == 3


def test_create_scythe_applies_user_agent_and_timeout() -> None:
    cfg = _config(user_agent="HarvesterUA/9", timeout=33.0)
    scythe = create_scythe(cfg)
    try:
        assert scythe.http_config.user_agent == "HarvesterUA/9"
        assert scythe.http_config.timeout == 33.0
    finally:
        scythe.close()


def test_robots_disallowed_fails_closed() -> None:
    cfg = _config(respect_robots_txt=True)
    fake_parser = MagicMock()
    fake_parser.can_fetch.return_value = False
    with (
        patch("middleware.oai_pmh.client.httpx.Client") as client_cls,
        patch("middleware.oai_pmh.client.RobotFileParser", return_value=fake_parser),
    ):
        client = client_cls.return_value.__enter__.return_value
        response = MagicMock()
        response.status_code = 200
        response.text = "User-agent: *\nDisallow: /\n"
        client.get.return_value = response
        with pytest.raises(OaiPmhRobotsDisallowedError):
            check_robots_allowed(cfg)


def test_robots_skipped_when_disabled() -> None:
    check_robots_allowed(_config(respect_robots_txt=False))


def test_rate_limiter_sleeps_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("middleware.oai_pmh.client.time.sleep", sleeps.append)
    clock = {"t": 100.0}

    def _mono() -> float:
        return clock["t"]

    monkeypatch.setattr("middleware.oai_pmh.client.time.monotonic", _mono)
    limiter = RateLimiter(max_requests_per_second=10.0)
    limiter.wait()
    clock["t"] = 100.05
    limiter.wait()
    assert sleeps and sleeps[0] == pytest.approx(0.05, rel=1e-3)
