"""Linked Data plugin unit tests."""

from collections.abc import AsyncGenerator
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fakes import BadFakeDataset, FakeSitemap, GoodFakeDataset
from rdflib import Graph

from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import NiceHttpClient, RobotsTxtDisallowedError
from middleware.harvester.plugin_base import HarvestedArc
from middleware.linked_data.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType
from middleware.linked_data.plugin import LinkedDataPlugin

EXPECTED_DATASET_COUNT = 5


def test_create_mapper_from_config() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=NiceHttpClientConfig(),
    )
    mapper = LinkedDataPlugin.create_mapper(config)
    assert mapper is not None


def test_create_mapper_rejects_unknown_payload_type() -> None:
    config = cast(Config, SimpleNamespace(payload_type="bad"))

    with pytest.raises(ValueError, match="Unsupported payload type"):
        LinkedDataPlugin.create_mapper(config)


def test_create_sitemap_rejects_unknown_sitemap_type() -> None:
    config = cast(Config, SimpleNamespace(sitemap_type="bad"))
    client = MagicMock()

    with pytest.raises(ValueError, match="Unsupported sitemap type"):
        LinkedDataPlugin.create_sitemap(config, client=client)


def test_create_dataset_class_rejects_unknown_dataset_type() -> None:
    config = cast(Config, SimpleNamespace(dataset_type="bad"))

    with pytest.raises(ValueError, match="Unsupported dataset type"):
        LinkedDataPlugin.create_dataset_class(config)


@pytest.mark.asyncio
async def test_linked_data_plugin_get_expected_datasets_returns_none_on_failure() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=NiceHttpClientConfig(),
    )

    class FakeSitemapFailure:
        def __init__(self, config: Config, client: NiceHttpClient) -> None:
            pass

        async def get_expected_count(self) -> int | None:
            raise RuntimeError("failed")

    def fake_create_sitemap(_config: Config, client: NiceHttpClient) -> FakeSitemapFailure:
        return FakeSitemapFailure(_config, client)

    with patch(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    ):
        result = await LinkedDataPlugin(config).get_expected_datasets()

    assert result is None


@pytest.mark.asyncio
async def test_linked_data_plugin_get_expected_datasets_returns_count() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=NiceHttpClientConfig(),
    )

    class FakeSitemapCount:
        def __init__(self, config: Config, client: NiceHttpClient) -> None:
            pass

        async def get_expected_count(self) -> int | None:
            return 5

    def fake_create_sitemap(_config: Config, client: NiceHttpClient) -> FakeSitemapCount:
        return FakeSitemapCount(_config, client)

    with patch(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    ):
        result = await LinkedDataPlugin(config).get_expected_datasets()

    assert result == EXPECTED_DATASET_COUNT


@pytest.mark.asyncio
async def test_linked_data_plugin_run_plugin_returns_record_processing_error_for_bad_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=NiceHttpClientConfig(),
    )

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FakeSitemap:
        del client
        return FakeSitemap(["https://example.org/dataset/fast"])

    mock_mapper = MagicMock()
    mock_mapper.map_graph.side_effect = lambda graph: HarvestedArc(arc_json=f"mapped:{graph}")

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr("middleware.linked_data.plugin.Dataset.registry", {DatasetType.html_jsonld: BadFakeDataset})
    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_mapper",
        staticmethod(lambda _config: mock_mapper),
    )

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)


@pytest.mark.asyncio
async def test_linked_data_plugin_run_plugin_returns_record_processing_error_for_mapping_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=NiceHttpClientConfig(),
    )

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FakeSitemap:
        del client
        return FakeSitemap(["https://example.org/dataset/fast"])

    mock_mapper = MagicMock()
    mock_mapper.map_graph.side_effect = ValueError("bad mapping")

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr("middleware.linked_data.plugin.Dataset.registry", {DatasetType.html_jsonld: GoodFakeDataset})
    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_mapper",
        staticmethod(lambda _config: mock_mapper),
    )

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)
    assert "Failed to map dataset" in str(results[0])
    assert results[0].record_id == "https://example.org/dataset/fast"


@pytest.mark.asyncio
async def test_linked_data_plugin_run_plugin_yields_skipped_record_for_duplicate_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=NiceHttpClientConfig(),
    )

    class DuplicateSitemap:
        def __init__(self, config: Config, client: NiceHttpClient) -> None:
            del config, client

        async def discover(self) -> AsyncGenerator[SkippedRecord, None]:
            yield SkippedRecord(
                "Duplicate discovery entry skipped: https://example.org/dataset/dup",
                "https://example.org/dataset/dup",
            )

        async def get_expected_count(self) -> int | None:
            return 1

    def create_duplicate_sitemap(_config: Config, client: NiceHttpClient) -> DuplicateSitemap:
        return DuplicateSitemap(_config, client)

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(create_duplicate_sitemap),
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_mapper",
        staticmethod(lambda _config: MagicMock()),
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.Dataset.registry",
        {DatasetType.html_jsonld: GoodFakeDataset},
    )

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], SkippedRecord)
    assert results[0].reason == "Duplicate discovery entry skipped: https://example.org/dataset/dup"
    assert results[0].url == "https://example.org/dataset/dup"


@pytest.mark.asyncio
async def test_linked_data_plugin_run_plugin_forwards_discovery_record_processing_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=NiceHttpClientConfig(),
    )

    class FailedDiscoverySitemap:
        def __init__(self, config: Config, client: NiceHttpClient) -> None:
            del config, client

        async def discover(self) -> AsyncGenerator[RecordProcessingError, None]:
            yield RecordProcessingError(
                "Regal /find record at from=0 index=1 is missing @id",
                "regal_find:from=0:index=1",
            )

        async def get_expected_count(self) -> int | None:
            return 1

    def create_failed_sitemap(_config: Config, client: NiceHttpClient) -> FailedDiscoverySitemap:
        return FailedDiscoverySitemap(_config, client)

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(create_failed_sitemap),
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_mapper",
        staticmethod(lambda _config: MagicMock()),
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.Dataset.registry",
        {DatasetType.html_jsonld: GoodFakeDataset},
    )

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)
    assert results[0].record_id == "regal_find:from=0:index=1"
    assert "missing @id" in str(results[0])


@pytest.mark.asyncio
async def test_linked_data_plugin_run_plugin_maps_valid_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=NiceHttpClientConfig(),
    )

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FakeSitemap:
        del client
        return FakeSitemap(["https://example.org/dataset/slow"])

    mock_mapper = MagicMock()
    mock_mapper.map_graph.return_value = HarvestedArc(arc_json="mapped:arc")

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr("middleware.linked_data.plugin.Dataset.registry", {DatasetType.html_jsonld: GoodFakeDataset})
    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_mapper",
        staticmethod(lambda _config: mock_mapper),
    )

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert results == [HarvestedArc(arc_json="mapped:arc", source_url="https://example.org/dataset/slow")]
    mock_mapper.map_graph.assert_called_once()
    (graph_arg,) = mock_mapper.map_graph.call_args.args
    assert isinstance(graph_arg, Graph)


@pytest.mark.asyncio
async def test_linked_data_plugin_run_plugin_returns_record_processing_error_when_robots_disallows_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.schema_org_general,
        http=NiceHttpClientConfig(),
    )

    def fake_create_sitemap(_config: Config, client: NiceHttpClient | None = None) -> FakeSitemap:
        del client
        return FakeSitemap(["https://example.org/dataset/slow"])

    monkeypatch.setattr(
        "middleware.linked_data.plugin.LinkedDataPlugin.create_sitemap",
        staticmethod(fake_create_sitemap),
    )
    monkeypatch.setattr(
        "middleware.linked_data.plugin.NiceHttpClient.ensure_allowed",
        AsyncMock(
            side_effect=RobotsTxtDisallowedError(
                "Dataset URL disallowed by robots.txt: https://example.org/dataset/slow"
            )
        ),
    )

    results = [item async for item in LinkedDataPlugin(config).run()]

    assert len(results) == 1
    assert isinstance(results[0], RecordProcessingError)
    assert "Dataset URL disallowed by robots.txt" in str(results[0])
