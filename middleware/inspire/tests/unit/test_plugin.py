"""Unit tests for the inspire plugin generator and config modules."""

# ruff: noqa: SLF001, PLR2004

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.plugin_base import HarvestedArc
from middleware.inspire.config import Config
from middleware.inspire.plugin import InspirePlugin
from middleware.payload.inspire.models import InspireRecord
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig, MapperType


def _mapper_config() -> MapperConfig:
    return MapperConfig(type=MapperType.inspire_general)


def _plugin_with_mock_mapper(mock_config: Config, mock_mapper: MagicMock) -> InspirePlugin:
    mock_mapper.accepts = PayloadKind.inspire_record
    with patch.object(InspirePlugin, "create_mapper", return_value=mock_mapper):
        return InspirePlugin(mock_config, _mapper_config())


def test_config_loading() -> None:
    # PluginConfig is a pure data container; instantiate directly
    config = Config(csw_url="https://csw.example.com")
    assert config.csw_url == "https://csw.example.com"


def test_config_verify_ssl_default_true() -> None:
    config = Config(csw_url="https://csw.example.com")
    assert config.verify_ssl is True


def test_config_verify_ssl_false() -> None:
    config = Config.model_validate({"csw_url": "https://csw.example.com", "verify_ssl": False})
    assert config.verify_ssl is False


def test_config_verify_ssl_ca_path() -> None:
    config = Config.model_validate({"csw_url": "https://csw.example.com", "verify_ssl": "/etc/ssl/certs/custom-ca.pem"})
    assert config.verify_ssl == "/etc/ssl/certs/custom-ca.pem"


def test_config_verify_ssl_coerces_quoted_bool_strings() -> None:
    """Quoted YAML/env strings must become bool, not a CA path."""
    for raw, expected in (
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("  false  ", False),
    ):
        config = Config.model_validate({"csw_url": "https://csw.example.com", "verify_ssl": raw})
        assert config.verify_ssl is expected, raw


def test_config_aliases_for_query() -> None:
    config = Config.model_validate({
        "csw_url": "https://csw.example.com",
        "query": "AnyText LIKE '%agriculture%'",
        "timeout": 10,
        "chunk_size": 1,
    })

    assert config.cql_query == "AnyText LIKE '%agriculture%'"
    assert config.xml_query is None


def test_config_aliases_for_xml_request() -> None:
    config = Config.model_validate({
        "csw_url": "https://csw.example.com",
        "xml_request": "<xml />",
        "timeout": 10,
        "chunk_size": 1,
    })

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

    mock_mapper = MagicMock()
    mock_mapper.map.return_value = [HarvestedArc(arc_json="{}", source_url="http://url")]

    with patch("middleware.inspire.plugin.CSWClient") as mock_csw_class:
        mock_csw = mock_csw_class.return_value
        mock_csw.__aenter__ = AsyncMock(return_value=mock_csw)
        mock_csw.__aexit__ = AsyncMock(return_value=None)
        mock_csw.get_records_async.return_value = _records()
        mock_csw.get_record_url.return_value = "http://url"

        plugin = _plugin_with_mock_mapper(mock_config, mock_mapper)
        results = [arc async for arc in plugin.run()]

        assert mock_csw.get_records_async.called
        assert len(results) == 1
        assert mock_mapper.map.called


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

    mock_mapper = MagicMock()
    with patch("middleware.inspire.plugin.CSWClient") as mock_csw_class:
        mock_csw = mock_csw_class.return_value
        mock_csw.__aenter__ = AsyncMock(return_value=mock_csw)
        mock_csw.__aexit__ = AsyncMock(return_value=None)
        mock_csw.get_records_async.return_value = _records()
        mock_csw.get_record_url.return_value = "http://url"

        plugin = _plugin_with_mock_mapper(mock_config, mock_mapper)
        results = [item async for item in plugin.run()]
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
        yield  # pragma: no cover  # noqa: make this an async generator

    mock_mapper = MagicMock()
    with patch("middleware.inspire.plugin.CSWClient") as mock_csw_class:
        mock_csw = mock_csw_class.return_value
        mock_csw.__aenter__ = AsyncMock(return_value=mock_csw)
        mock_csw.__aexit__ = AsyncMock(return_value=None)
        mock_csw.get_records_async.return_value = _records()

        plugin = _plugin_with_mock_mapper(mock_config, mock_mapper)
        with pytest.raises(RuntimeError, match="CSW endpoint unreachable"):
            async for _ in plugin.run():
                pass


@pytest.mark.asyncio
async def test_run_plugin_skips_non_dataset_hierarchy() -> None:
    mock_config = MagicMock(spec=Config)
    mock_config.csw_url = "https://csw.example.com"
    mock_config.cql_query = None
    mock_config.xml_query = None
    mock_config.chunk_size = 10

    service_record = MagicMock(spec=InspireRecord)
    service_record.identifier = "svc-1"
    service_record.hierarchy = "service"

    dataset_record = MagicMock(spec=InspireRecord)
    dataset_record.identifier = "ds-1"
    dataset_record.hierarchy = "dataset"

    async def _records() -> AsyncGenerator[InspireRecord, None]:
        yield service_record
        yield dataset_record

    mock_mapper = MagicMock()
    mock_mapper.map.return_value = [
        HarvestedArc(
            arc_json="{}",
            source_url="http://csw/ds-1",
            identifier="ds-1",
            studies=1,
            assays=1,
        )
    ]

    with patch("middleware.inspire.plugin.CSWClient") as mock_csw_class:
        mock_csw = mock_csw_class.return_value
        mock_csw.__aenter__ = AsyncMock(return_value=mock_csw)
        mock_csw.__aexit__ = AsyncMock(return_value=None)
        mock_csw.get_records_async.return_value = _records()
        mock_csw.get_record_url.side_effect = lambda ident: f"http://csw/{ident}"

        plugin = _plugin_with_mock_mapper(mock_config, mock_mapper)
        results = [item async for item in plugin.run()]

    assert len(results) == 2
    assert isinstance(results[0], SkippedRecord)
    assert "hierarchy level: service" in results[0].reason
    assert results[0].url == "http://csw/svc-1"
    assert results[1] == HarvestedArc(
        arc_json="{}",
        source_url="http://csw/ds-1",
        identifier="ds-1",
        studies=1,
        assays=1,
    )


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

    mock_mapper = MagicMock()
    with patch("middleware.inspire.plugin.CSWClient", return_value=mock_client):
        plugin = _plugin_with_mock_mapper(mock_config, mock_mapper)
        result = await plugin.get_expected_datasets()

    assert result == 42
