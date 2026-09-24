"""Scythe client construction, robots preflight, and optional rate limiting."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx
from oaipmh_scythe import HTTPConfig, RetryConfig, Scythe

from middleware.oai_pmh.config import Config
from middleware.oai_pmh.errors import OaiPmhRobotsDisallowedError

logger = logging.getLogger(__name__)


def build_http_config(config: Config) -> HTTPConfig:
    """Map plugin HTTP fields onto Scythe ``HTTPConfig``."""
    return HTTPConfig(
        timeout=config.timeout,
        user_agent=config.user_agent,
    )


def build_retry_config(config: Config) -> RetryConfig:
    """Map plugin retry fields onto Scythe ``RetryConfig``."""
    return RetryConfig(
        max_retries=config.max_retries,
        retry_status_codes=config.retry_status_codes,
        default_retry_after=config.default_retry_after,
        retry_on_transport_error=config.retry_on_transport_error,
        initial_backoff=config.initial_backoff,
    )


def create_scythe(config: Config) -> Scythe:
    """Construct a Scythe client from plugin configuration."""
    return Scythe(
        config.endpoint_url,
        http_config=build_http_config(config),
        retry_config=build_retry_config(config),
    )


_HTTP_CLIENT_ERROR = 400


def check_robots_allowed(config: Config) -> None:
    """Fail closed when ``respect_robots_txt`` and robots.txt disallows the endpoint."""
    if not config.respect_robots_txt:
        return
    parsed = urlparse(config.endpoint_url)
    if not parsed.scheme or not parsed.netloc:
        raise OaiPmhRobotsDisallowedError(f"Cannot evaluate robots.txt for invalid endpoint: {config.endpoint_url}")
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    parser = RobotFileParser()
    try:
        with httpx.Client(timeout=config.timeout, headers={"User-Agent": config.user_agent}) as client:
            response = client.get(robots_url, follow_redirects=True)
            if response.status_code >= _HTTP_CLIENT_ERROR:
                logger.info(
                    "robots.txt unavailable for %s (HTTP %s); assuming allow.",
                    parsed.netloc,
                    response.status_code,
                )
                return
            parser.parse(response.text.splitlines())
    except httpx.HTTPError as exc:
        logger.info("Failed to fetch robots.txt for %s: %s; assuming allow.", parsed.netloc, exc)
        return

    path = parsed.path or "/"
    if not parser.can_fetch(config.user_agent, path):
        raise OaiPmhRobotsDisallowedError(
            f"robots.txt disallows OAI endpoint {config.endpoint_url} for user agent {config.user_agent}"
        )


@dataclass
class RateLimiter:
    """Simple per-host minimum interval between Scythe requests."""

    max_requests_per_second: float | None
    _last_request_at: float = field(default=0.0, init=False)

    def wait(self) -> None:
        """Sleep when needed to honour ``max_requests_per_second``."""
        if self.max_requests_per_second is None or self.max_requests_per_second <= 0:
            return
        min_interval = 1.0 / self.max_requests_per_second
        now = time.monotonic()
        elapsed = now - self._last_request_at
        if self._last_request_at > 0 and elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_at = time.monotonic()
