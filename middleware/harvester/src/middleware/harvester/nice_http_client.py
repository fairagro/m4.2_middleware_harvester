"""Shared HTTP client wrapper with polite harvesting support."""

import asyncio
import logging
import random
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Annotated, Any
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

_HTTP_STATUS_SERVER_ERROR_MIN = 500


class NiceHttpClientConfig(BaseModel):
    """Shared HTTP client configuration for polite harvesting."""

    model_config = ConfigDict(populate_by_name=True)

    connect_timeout: Annotated[float, Field(description="HTTP connect timeout seconds.", ge=1)] = 10.0
    read_timeout: Annotated[float, Field(description="HTTP read timeout seconds.", ge=1)] = 30.0
    max_connections: Annotated[
        int,
        Field(
            description="Maximum number of concurrent HTTP connections used for HTTP requests.",
            ge=1,
        ),
    ] = 10
    retry_attempts: Annotated[
        int,
        Field(
            description="Maximum number of retry attempts for transient request failures. 0 disables retries.",
            ge=0,
        ),
    ] = 5
    retry_backoff_base: Annotated[
        float,
        Field(
            description="Base delay in seconds for retry backoff.",
            gt=0,
        ),
    ] = 1.0
    retry_backoff_factor: Annotated[
        float,
        Field(
            description="Exponential backoff factor applied to retry delays.",
            ge=1,
        ),
    ] = 2.0
    max_retry_delay: Annotated[
        float,
        Field(
            description=(
                "Maximum delay in seconds used to cap both Retry-After header values "
                "and locally calculated exponential backoff delays."
            ),
            ge=0,
        ),
    ] = 600.0
    user_agent: Annotated[
        str,
        Field(description="User-Agent header value used for all outgoing requests."),
    ] = "FAIRagro-Harvester/2.0 (dataservice@fairagro.org)"
    max_requests_per_second: Annotated[
        float | None,
        Field(
            description=(
                "Maximum number of requests per second sent to the same host. "
                "Set to None to disable host rate limiting."
            ),
            ge=0,
        ),
    ] = 2.0
    respect_robots_txt: Annotated[
        bool,
        Field(description="Respect robots.txt directives when fetching URLs."),
    ] = True


class RobotsTxtCache:
    """Cache robots.txt state and enforce per-host polite delays."""

    def __init__(self) -> None:
        """Initialize the robots.txt cache and per-host scheduling state."""
        self.robots_cache: dict[str, RobotFileParser | None] = {}
        self.host_crawl_delay: dict[str, float] = {}
        self.host_last_request: dict[str, float] = {}
        self.host_locks: dict[str, asyncio.Lock] = {}

    @staticmethod
    def _host_from_url(url: str) -> tuple[str, str]:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")
        return parsed.scheme, parsed.netloc

    def host_from_url(self, url: str) -> tuple[str, str]:
        """Extract and return the normalized scheme and host from a URL."""
        return self._host_from_url(url)

    async def wait_for_host(self, host: str, max_requests_per_second: float | None) -> None:
        """Respect the host crawl delay and optional rate limit before the next request."""
        lock = self.host_locks.setdefault(host, asyncio.Lock())
        async with lock:
            now = time.monotonic()
            if max_requests_per_second is None or max_requests_per_second <= 0:
                delay = 0.0
            else:
                delay = 1.0 / max_requests_per_second

            crawl_delay = self.host_crawl_delay.get(host)
            if crawl_delay is not None:
                delay = max(delay, crawl_delay)

            last_request = self.host_last_request.get(host, 0.0)
            wait = delay - (now - last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self.host_last_request[host] = time.monotonic()

    async def _fetch_robots_txt(
        self,
        scheme: str,
        host: str,
        http_client: httpx.AsyncClient,
        config: NiceHttpClientConfig,
    ) -> RobotFileParser | None:
        if host in self.robots_cache:
            return self.robots_cache[host]

        if not config.respect_robots_txt:
            self.robots_cache[host] = None
            return None

        parser = RobotFileParser()
        robots_url = urlunparse((scheme, host, "/robots.txt", "", "", ""))

        await self.wait_for_host(host, config.max_requests_per_second)
        try:
            response = await http_client.get(robots_url, follow_redirects=True)
            if response.is_error:
                raise ValueError(f"HTTP {response.status_code}")
            parser.parse(response.text.splitlines())
            parser.set_url(robots_url)
            self.robots_cache[host] = parser
            crawl_delay = parser.crawl_delay(config.user_agent)
            if crawl_delay is not None:
                self.host_crawl_delay[host] = float(crawl_delay)
            return parser
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to fetch robots.txt for host %s: %s; assuming allow all.",
                host,
                exc,
            )
            self.robots_cache[host] = None
            return None

    async def is_allowed(
        self,
        url: str,
        http_client: httpx.AsyncClient,
        config: NiceHttpClientConfig,
    ) -> bool:
        """Determine whether the given URL is allowed by robots.txt."""
        scheme, host = self._host_from_url(url)
        parser = await self._fetch_robots_txt(scheme, host, http_client, config)
        if parser is None:
            return True
        return parser.can_fetch(config.user_agent, url)


class RobotsTxtDisallowedError(RuntimeError):
    """Indicates a URL is disallowed by robots.txt for the configured user agent."""


class NiceHttpClient:
    """Async HTTP client wrapper that applies polite harvesting policies."""

    def __init__(self, config: NiceHttpClientConfig, transport: httpx.AsyncBaseTransport | None = None) -> None:
        """Initialize the shared HTTP client wrapper with optional transport."""
        self._config = config
        self._transport = transport
        self._client: httpx.AsyncClient | None = None
        self._robots = RobotsTxtCache()

    async def __aenter__(self) -> "NiceHttpClient":
        """Open the underlying httpx client and return this wrapper."""
        self._client = httpx.AsyncClient(
            transport=self._transport,
            timeout=httpx.Timeout(
                connect=self._config.connect_timeout,
                read=self._config.read_timeout,
                write=None,
                pool=None,
            ),
            limits=httpx.Limits(
                max_connections=self._config.max_connections,
                max_keepalive_connections=self._config.max_connections,
            ),
            headers={"User-Agent": self._config.user_agent},
        )
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: Any | None
    ) -> None:
        """Close the underlying httpx client when the context exits."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Return the underlying httpx.AsyncClient instance."""
        assert self._client is not None, "NiceHttpClient must be used as an async context manager"
        return self._client

    async def is_allowed(self, url: str) -> bool:
        """Return whether the URL is allowed by robots.txt for this client configuration."""
        if not self._config.respect_robots_txt:
            return True
        return await self._robots.is_allowed(url, self.client, self._config)

    async def ensure_allowed(self, url: str) -> None:
        """Raise if the URL is disallowed by robots.txt."""
        if not self._config.respect_robots_txt:
            return
        if not await self.is_allowed(url):
            logger.warning(
                "robots.txt disallows URL %s for user agent %s",
                url,
                self._config.user_agent,
            )
            raise RobotsTxtDisallowedError(f"Dataset URL disallowed by robots.txt: {url}")

    @staticmethod
    def _calculate_retry_delay(config: NiceHttpClientConfig, attempt: int) -> float:
        delay = config.retry_backoff_base * (config.retry_backoff_factor ** (attempt - 1))
        return min(delay * random.uniform(0.9, 1.1), config.max_retry_delay)

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        if not value:
            return None

        clean_value = value.strip()
        if clean_value.isdigit():
            return float(clean_value)

        try:
            retry_date = parsedate_to_datetime(clean_value)
        except (TypeError, ValueError):
            return None

        if retry_date.tzinfo is None:
            retry_date = retry_date.replace(tzinfo=UTC)

        seconds = (retry_date - datetime.now(UTC)).total_seconds()
        return seconds if seconds > 0 else 0.0

    @staticmethod
    async def retry_get_with_client(
        client: httpx.AsyncClient,
        config: NiceHttpClientConfig,
        url: str,
        follow_redirects: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform a GET request with retry/backoff semantics using an existing AsyncClient."""
        total_attempts = 1 + config.retry_attempts
        last_error: Exception | None = None
        response: httpx.Response | None = None

        for attempt in range(1, total_attempts + 1):
            try:
                response = await client.get(url, follow_redirects=follow_redirects, **kwargs)
            except httpx.RequestError as exc:
                last_error = exc
            else:
                if response.status_code in {429, 503} or response.status_code >= _HTTP_STATUS_SERVER_ERROR_MIN:
                    last_error = httpx.HTTPStatusError(
                        f"Transient HTTP error {response.status_code} for {url}",
                        request=response.request,
                        response=response,
                    )
                elif response.is_error:
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code} for {url}",
                        request=response.request,
                        response=response,
                    )
                else:
                    return response

            if attempt == total_attempts:
                logger.error("Failed to GET %s after %d attempts: %s", url, total_attempts, last_error)
                assert last_error is not None
                raise last_error

            delay = NiceHttpClient._calculate_retry_delay(config, attempt)
            if response is not None and response.status_code in {429, 503}:
                retry_after = NiceHttpClient._parse_retry_after(response.headers.get("Retry-After"))
                if retry_after is not None:
                    delay = min(max(delay, retry_after), config.max_retry_delay)

            await asyncio.sleep(delay)

        raise RuntimeError("retry_get terminated unexpectedly")

    async def get_with_policy(self, url: str, follow_redirects: bool = True, **kwargs: Any) -> httpx.Response:
        """Fetch the URL through robots.txt, host rate limiting, and retry/backoff policy."""
        await self.ensure_allowed(url)
        await self.wait_for_host(url)
        return await self.retry_get_with_client(self.client, self._config, url, follow_redirects, **kwargs)

    async def wait_for_host(self, url: str) -> None:
        """Wait for the configured per-host delay before the next request."""
        _, host = self._robots.host_from_url(url)
        await self._robots.wait_for_host(host, self._config.max_requests_per_second)
