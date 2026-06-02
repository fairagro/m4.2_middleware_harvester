"""Unit tests for the inspire plugin generator and config modules."""

# ruff: noqa: SLF001, PLR2004

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from middleware.harvester.errors import RecordProcessingError
from middleware.inspire.config import Config
from middleware.inspire.models import InspireRecord
from middleware.inspire.plugin import InspirePlugin


def test_config_loading() -> None:
    # PluginConfig is a pure data container; instantiate directly
    config = Config(csw_url="https://csw.example.com")
    assert config.csw_url == "https://csw.example.com"


def test_config_aliases_for_query() -> None:
    config = Config.model_validate(
        {
            "csw_url": "https://csw.example.com",
            "query": "AnyText LIKE '%agriculture%'",
            "timeout": 10,
            "chunk_size": 1,
        }
    )

    assert config.cql_query == "AnyText LIKE '%agriculture%'"
    assert config.xml_query is None


def test_config_aliases_for_xml_request() -> None:
    config = Config.model_validate(
        {
            "csw_url": "https://csw.example.com",
            "xml_request": "<xml />",
            "timeout": 10,
            "chunk_size": 1,
        }
    )

    assert config.cql_query is None
    assert config.xml_query == "<xml />"


@pytest.mark.asyncio
async def test_run_plugin_success() -> None:
    mock_config = MagicMock(spec=Config)
    mock_config.csw_url = "https://csw.example.com"
    mock_config.cql_query = None
    mock_config.xml_query = None
    mock_config.chunk_size = 10

    mock_record = MagicMock(spec=InspireRecord)
    mock_record.identifier = "rec-1"
    mock_record.hierarchy = "dataset"
    mock_record.title = "Test"

    mock_records = [mock_record]

    async def _records() -> AsyncGenerator[InspireRecord, None]:
        for record in mock_records:
            yield record

    with (
        patch("middleware.inspire.plugin.CSWClient") as mock_csw_class,
        patch("middleware.inspire.plugin.InspireMapper") as mock_mapper_class,
    ):
        mock_csw = mock_csw_class.return_value
        mock_csw.__aenter__ = AsyncMock(return_value=mock_csw)
        mock_csw.__aexit__ = AsyncMock(return_value=None)
        mock_csw.get_records_async.return_value = _records()
        mock_csw.get_record_url.return_value = "http://url"

        mock_mapper = mock_mapper_class.return_value
        mock_mapper.map_record.return_value = MagicMock()

        # Consume the generator
        results = [arc async for arc in InspirePlugin(mock_config).run()]

        assert mock_csw.get_records_async.called
        assert len(results) == 1


@pytest.mark.asyncio
async def test_run_plugin_with_error() -> None:
    mock_config = MagicMock(spec=Config)
    mock_config.csw_url = "https://csw.example.com"
    mock_config.cql_query = None
    mock_config.xml_query = None
    mock_config.chunk_size = 10

    mock_error = RecordProcessingError("Failed", record_id="err-1")
    mock_records = [mock_error]

    async def _records() -> AsyncGenerator[RecordProcessingError, None]:
        for item in mock_records:
            yield item

    with patch("middleware.inspire.plugin.CSWClient") as mock_csw_class:
        mock_csw = mock_csw_class.return_value
        mock_csw.__aenter__ = AsyncMock(return_value=mock_csw)
        mock_csw.__aexit__ = AsyncMock(return_value=None)
        mock_csw.get_records_async.return_value = _records()
        mock_csw.get_record_url.return_value = "http://url"

        results = [item async for item in InspirePlugin(mock_config).run()]
        # Should yield the error object explicitly to the orchestrator
        assert len(results) == 1
        assert isinstance(results[0], RecordProcessingError)


@pytest.mark.asyncio
async def test_run_plugin_fatal_error_propagates() -> None:
    mock_config = MagicMock(spec=Config)
    mock_config.csw_url = "https://csw.example.com"
    mock_config.cql_query = None
    mock_config.xml_query = None
    mock_config.chunk_size = 10

    async def _records() -> AsyncGenerator[str, None]:
        raise RuntimeError("CSW endpoint unreachable")
        yield  # pragma: no cover

    with patch("middleware.inspire.plugin.CSWClient") as mock_csw_class:
        mock_csw = mock_csw_class.return_value
        mock_csw.__aenter__ = AsyncMock(return_value=mock_csw)
        mock_csw.__aexit__ = AsyncMock(return_value=None)
        mock_csw.get_records_async.return_value = _records()

        with pytest.raises(RuntimeError, match="CSW endpoint unreachable"):
            async for _ in InspirePlugin(mock_config).run():
                pass


@pytest.mark.asyncio
async def test_get_expected_datasets_returns_count() -> None:
    mock_config = MagicMock(spec=Config)
    mock_config.csw_url = "https://csw.example.com"
    mock_config.cql_query = None
    mock_config.xml_query = None
    mock_config.chunk_size = 10

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get_record_count_async = AsyncMock(return_value=42)

    with patch("middleware.inspire.plugin.CSWClient", return_value=mock_client):
        result = await InspirePlugin(mock_config).get_expected_datasets()

    assert result == 42
