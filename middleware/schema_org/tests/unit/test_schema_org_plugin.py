"""Unit tests for the Schema.org plugin entrypoint."""

from typing import Any

import pytest

from middleware.schema_org.config import Config
from middleware.schema_org.plugin import run_plugin


class DummyConfig(Config):
    """A dummy config class used to satisfy plugin config typing in tests."""

    pass


@pytest.mark.asyncio
async def test_run_plugin_yields_arc(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: Patch fetch_json_data to return a valid dataset
    dataset = {
        "@id": "10.1234/test",
        "name": "Test Dataset",
        "description": "A test dataset.",
        "creator": [{"givenName": "Alice", "familyName": "Smith"}],
        "url": "https://example.org/dataset/10.1234/test",
        "license": "CC-BY-4.0",
        "inLanguage": "en",
        "publisher": {"name": "Test Publisher"},
        "keywords": ["soil", "plant", "experiment"],
    }

    async def fake_fetch_json_data(_config: Any) -> list[dict[str, Any]]:
        return [dataset]

    monkeypatch.setattr("middleware.schema_org.plugin.fetch_json_data", fake_fetch_json_data)
    config = Config(json_source_url="http://dummy", json_source_type="url")

    # Act
    results = []
    async for result in run_plugin(config):
        results.append(result)

    # Assert
    assert len(results) == 1
    assert isinstance(results[0], str)
    assert "Test Dataset" in results[0]


@pytest.mark.asyncio
async def test_run_plugin_yields_error_on_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: Patch fetch_json_data to return invalid data
    async def fake_fetch_json_data(_config: Any) -> list[Any]:
        return [123]  # Not a dict

    monkeypatch.setattr("middleware.schema_org.plugin.fetch_json_data", fake_fetch_json_data)
    config = Config(json_source_url="http://dummy", json_source_type="url")

    # Act
    results = []
    async for result in run_plugin(config):
        results.append(result)

    # Assert
    assert len(results) == 1
    assert hasattr(results[0], "__class__")
    assert "Failed to map dataset" in str(results[0])


@pytest.mark.asyncio
async def test_run_plugin_yields_error_on_nonlist(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: Patch fetch_json_data to return a dict instead of list
    async def fake_fetch_json_data(_config: Any) -> dict[str, Any]:
        return {"foo": "bar"}

    monkeypatch.setattr("middleware.schema_org.plugin.fetch_json_data", fake_fetch_json_data)
    config = Config(json_source_url="http://dummy", json_source_type="url")

    # Act
    results = []
    async for result in run_plugin(config):
        results.append(result)

    # Assert
    assert len(results) == 1
    assert hasattr(results[0], "__class__")
    assert "JSON data must be a list" in str(results[0])
