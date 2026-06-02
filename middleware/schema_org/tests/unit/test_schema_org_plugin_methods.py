"""Schema.org plugin unit tests."""

from collections.abc import AsyncGenerator
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from test_fakes import BadFakeDataset, FakeSitemap, GoodFakeDataset

from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import RobotsTxtDisallowedError
from middleware.schema_org.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType
from middleware.schema_org.dataset import DuplicateUrlDiscoveryResult
from middleware.schema_org.plugin import SchemaOrgPlugin

EXPECTED_DATASET_COUNT = 5


def test_create_mapper_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )
    mapper = SchemaOrgPlugin.create_mapper(config)
    assert mapper is not None


def test_create_mapper_rejects_unknown_payload_type() -> None:
    config = cast(Config, SimpleNamespace(payload_type="bad"))

    with pytest.raises(ValueError, match="Unsupported payload type"):
        SchemaOrgPlugin.create_mapper(config)


def test_create_sitemap_rejects_unknown_sitemap_type() -> None:
    config = cast(Config, SimpleNamespace(sitemap_type="bad"))
    client = MagicMock()

    with pytest.raises(ValueError, match="Unsupported sitemap type"):
        SchemaOrgPlugin.create_sitemap(config, client=client)


def test_extract_arc_identifier_handles_list_identifiers() -> None:
    arc_json = '{"@graph":[{"@id":"./","identifier":["10.1234/abc"]}]}'
    result = SchemaOrgPlugin._extract_arc_identifier(arc_json)  # noqa: SLF001
    assert result == "10.1234/abc"


@pytest.mark.asyncio
async def test_schema_org_plugin_get_expected_datasets_returns_none_on_failure() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )

    class FakeSitemapFailure:
        def __init__(self, config: Config, client: object) -> None:
            pass

        async def get_expected_count(self) -> int | None:
            raise RuntimeError("failed")

    def fake_create_sitemap(_config: Config, client: object) -> FakeSitemapFailure:
        return FakeSitemapFailure(_config, client)

    with patch(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    ):
        result = await SchemaOrgPlugin(config).get_expected_datasets()

    assert result is None


@pytest.mark.asyncio
async def test_schema_org_plugin_get_expected_datasets_returns_count() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )

    class FakeSitemapCount:
        def __init__(self, config: Config, client: object) -> None:
            pass

        async def get_expected_count(self) -> int | None:
            return 5

    def fake_create_sitemap(_config: Config, client: object) -> FakeSitemapCount:
        return FakeSitemapCount(_config, client)

    with patch(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    ):
        result = await SchemaOrgPlugin(config).get_expected_datasets()

    assert result == EXPECTED_DATASET_COUNT


@pytest.mark.asyncio
async def test_schema_org_plugin_run_plugin_returns_record_processing_error_for_bad_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )

    def fake_create_sitemap(_config: Config, **_kwargs: object) -> FakeSitemap:
        return FakeSitemap(["https://example.org/dataset/fast"])

    mock_mapper = MagicMock()
    mock_mapper.map_graph.side_effect = lambda graph: f"mapped:{graph}"

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr("middleware.schema_org.plugin.Dataset.registry", {DatasetType.html_jsonld: BadFakeDataset})
    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_mapper",
        staticmethod(lambda _config: mock_mapper),
    )

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)


@pytest.mark.asyncio
async def test_schema_org_plugin_run_plugin_yields_skipped_record_for_duplicate_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )

    class DuplicateSitemap:
        def __init__(self, config: Config, client: object) -> None:
            del config, client

        async def discover(self) -> AsyncGenerator[DuplicateUrlDiscoveryResult, None]:
            yield DuplicateUrlDiscoveryResult("https://example.org/dataset/dup")

        async def get_expected_count(self) -> int | None:
            return 1

    def create_duplicate_sitemap(_config: Config, client: object) -> DuplicateSitemap:
        return DuplicateSitemap(_config, client)

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(create_duplicate_sitemap),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_mapper",
        staticmethod(lambda _config: MagicMock()),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.Dataset.registry",
        {DatasetType.html_jsonld: GoodFakeDataset},
    )

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], SkippedRecord)
    assert results[0].reason == "Duplicate sitemap entry skipped: https://example.org/dataset/dup"
    assert results[0].url == "https://example.org/dataset/dup"


@pytest.mark.asyncio
async def test_schema_org_plugin_run_plugin_maps_valid_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )

    def fake_create_sitemap(_config: Config, **_kwargs: object) -> FakeSitemap:
        return FakeSitemap(["https://example.org/dataset/slow"])

    mock_mapper = MagicMock()
    mock_mapper.map_graph.side_effect = lambda graph: f"mapped:{graph}"

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr("middleware.schema_org.plugin.Dataset.registry", {DatasetType.html_jsonld: GoodFakeDataset})
    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_mapper",
        staticmethod(lambda _config: mock_mapper),
    )

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert results == [("mapped:graph:https://example.org/dataset/slow", "https://example.org/dataset/slow")]


@pytest.mark.asyncio
async def test_schema_org_plugin_run_plugin_returns_record_processing_error_when_robots_disallows_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )

    def fake_create_sitemap(_config: Config, **_kwargs: object) -> FakeSitemap:
        return FakeSitemap(["https://example.org/dataset/slow"])

    monkeypatch.setattr(
        "middleware.schema_org.plugin.SchemaOrgPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr(
        "middleware.schema_org.plugin.NiceHttpClient.ensure_allowed",
        AsyncMock(
            side_effect=RobotsTxtDisallowedError(
                "Dataset URL disallowed by robots.txt: https://example.org/dataset/slow"
            )
        ),
    )

    results = [item async for item in SchemaOrgPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)
    assert "Dataset URL disallowed by robots.txt" in str(results[0])
