"""Schema.org HTML+JSON-LD dataset unit tests."""

import asyncio
import contextlib
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from test_fakes import _MINIMAL_CONFIG, BAD_JSON_HTML, MULTI_BLOCK_HTML, NO_JSONLD_HTML, SIMPLE_HTML

from middleware.harvester.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.schema_org.config import Config, DatasetType, PayloadType, SitemapType
from middleware.schema_org.dataset.html_jsonld import HtmlJsonLdDataset
from middleware.schema_org.errors import SchemaOrgDatasetError

EXPECTED_RETRY_CALLS = 2
MAX_BACKOFF_DELAY_SECONDS = 0.5


def test_html_jsonld_dataset_identifier() -> None:
    async def run() -> None:
        async with NiceHttpClient(NiceHttpClientConfig()) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, _MINIMAL_CONFIG)
            assert ds.identifier == "https://example.org/page"

    asyncio.run(run())


def test_html_jsonld_dataset_to_graph_single_block() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SIMPLE_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        async with NiceHttpClient(NiceHttpClientConfig(), transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, _MINIMAL_CONFIG)
            graph = await ds.to_graph()
            return len(graph)

    triple_count = asyncio.run(run())
    assert triple_count > 0


def test_html_jsonld_dataset_to_graph_merges_multiple_blocks() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=MULTI_BLOCK_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        async with NiceHttpClient(NiceHttpClientConfig(), transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, _MINIMAL_CONFIG)
            graph = await ds.to_graph()
            return len(graph)

    triple_count = asyncio.run(run())
    assert triple_count > 0


def test_html_jsonld_dataset_raises_on_no_jsonld_blocks() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=NO_JSONLD_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with NiceHttpClient(NiceHttpClientConfig(), transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, _MINIMAL_CONFIG)
            await ds.to_graph()

    with pytest.raises(SchemaOrgDatasetError, match="No JSON-LD blocks"):
        asyncio.run(run())


def test_html_jsonld_dataset_raises_on_http_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with NiceHttpClient(NiceHttpClientConfig(), transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, _MINIMAL_CONFIG)
            await ds.to_graph()

    with pytest.raises(SchemaOrgDatasetError, match="HTTP 404"):
        asyncio.run(run())


def test_html_jsonld_dataset_raises_on_invalid_json() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=BAD_JSON_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with NiceHttpClient(NiceHttpClientConfig(), transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, _MINIMAL_CONFIG)
            await ds.to_graph()

    with pytest.raises(SchemaOrgDatasetError, match="Invalid JSON"):
        asyncio.run(run())


def test_html_jsonld_dataset_invalid_json_error_includes_block() -> None:
    invalid_block = '{"@context": "https://schema.org", "@type": "Dataset", invalid}'
    html = f"""<!DOCTYPE html>
<html>
<head>
  <script type="application/ld+json">
  {invalid_block}
  </script>
</head>
<body></body>
</html>"""

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> None:
        async with NiceHttpClient(NiceHttpClientConfig(), transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, _MINIMAL_CONFIG)
            await ds.to_graph()

    with pytest.raises(SchemaOrgDatasetError) as exc_info:
        asyncio.run(run())

    assert invalid_block in str(exc_info.value)


def test_html_jsonld_dataset_follows_redirects() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL("https://doi.org/10.5447/ipk/2024/11"):
            return httpx.Response(302, headers={"location": "https://doi.ipk-gatersleben.de/actual"})
        if request.url == httpx.URL("https://doi.ipk-gatersleben.de/actual"):
            return httpx.Response(200, text=SIMPLE_HTML, headers={"content-type": "text/html"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        async with NiceHttpClient(NiceHttpClientConfig(), transport=transport) as client:
            ds = HtmlJsonLdDataset("https://doi.org/10.5447/ipk/2024/11", client, _MINIMAL_CONFIG)
            graph = await ds.to_graph()
            return len(graph)

    triple_count = asyncio.run(run())
    assert triple_count > 0


def test_html_jsonld_dataset_retries_transient_server_error() -> None:
    call_count = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(503)
        return httpx.Response(200, text=SIMPLE_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        config = Config(
            sitemap_url="https://example.org/sitemap.xml",
            sitemap_type=SitemapType.xml,
            dataset_type=DatasetType.html_jsonld,
            payload_type=PayloadType.general,
            http=NiceHttpClientConfig(
                retry_attempts=1,
                retry_backoff_base=0.01,
                retry_backoff_factor=1.0,
            ),
        )
        async with NiceHttpClient(config.http, transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, config=config)
            graph = await ds.to_graph()
            return len(graph)

    triple_count = asyncio.run(run())
    assert triple_count > 0
    assert call_count == EXPECTED_RETRY_CALLS


def test_html_jsonld_dataset_uses_retry_after_header_if_present() -> None:
    call_count = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, text=SIMPLE_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        config = Config(
            sitemap_url="https://example.org/sitemap.xml",
            sitemap_type=SitemapType.xml,
            dataset_type=DatasetType.html_jsonld,
            payload_type=PayloadType.general,
            http=NiceHttpClientConfig(
                retry_attempts=1,
                retry_backoff_base=0.01,
                retry_backoff_factor=1.0,
                max_retry_delay=0.01,
            ),
        )
        async with NiceHttpClient(config.http, transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, config=config)
            graph = await ds.to_graph()
            return len(graph)

    triple_count = asyncio.run(run())
    assert triple_count > 0
    assert call_count == EXPECTED_RETRY_CALLS


def test_html_jsonld_dataset_caps_backoff_delay() -> None:
    call_delays: list[float] = []

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    transport = httpx.MockTransport(handler)

    async def fake_sleep(delay: float) -> None:
        call_delays.append(delay)

    async def run() -> None:
        config = Config(
            sitemap_url="https://example.org/sitemap.xml",
            sitemap_type=SitemapType.xml,
            dataset_type=DatasetType.html_jsonld,
            payload_type=PayloadType.general,
            http=NiceHttpClientConfig(
                retry_attempts=1,
                retry_backoff_base=10.0,
                retry_backoff_factor=2.0,
                max_retry_delay=0.5,
            ),
        )
        async with NiceHttpClient(config.http, transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, config=config)
            with (
                patch("middleware.schema_org.dataset.html_jsonld.asyncio.sleep", new=fake_sleep),
                contextlib.suppress(SchemaOrgDatasetError),
            ):
                await ds.to_graph()

    asyncio.run(run())
    assert call_delays
    assert all(delay <= MAX_BACKOFF_DELAY_SECONDS for delay in call_delays)


@pytest.mark.asyncio
async def test_html_jsonld_dataset_offloads_large_jsonld_to_thread() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SIMPLE_HTML, headers={"content-type": "text/html"})

    transport = httpx.MockTransport(handler)

    async def run() -> int:
        config = Config(
            sitemap_url="https://example.org/sitemap.xml",
            sitemap_type=SitemapType.xml,
            dataset_type=DatasetType.html_jsonld,
            payload_type=PayloadType.general,
            http=NiceHttpClientConfig(),
            jsonld_parse_threshold_bytes=1,
        )
        async with NiceHttpClient(NiceHttpClientConfig(), transport=transport) as client:
            ds = HtmlJsonLdDataset("https://example.org/page", client, config)
            with patch(
                "middleware.schema_org.dataset.html_jsonld.asyncio.to_thread",
                new=AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)),
            ) as to_thread_mock:
                graph = await ds.to_graph()
                assert to_thread_mock.called
                return len(graph)

    assert await run() > 0
