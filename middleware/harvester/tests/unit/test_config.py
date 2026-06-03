"""Unit tests for the Harvester orchestrator configuration."""

import pytest
from pydantic import ValidationError

from middleware.api_client.config import Config as ApiClientConfig
from middleware.harvester.config import Config, RepositoryConfig
from middleware.harvester.nice_http_client import NiceHttpClientConfig
from middleware.inspire.config import Config as InspireConfig


def test_harvester_config_loading() -> None:
    """Test loading and validating the root harvester config using the keyed-map format."""
    raw_config = {
        "api_client": {
            "api_url": "https://api.example.com",
        },
        "repositories": [
            {
                "rdi": "test-import",
                "inspire": {
                    "csw_url": "https://csw.example.com",
                },
            }
        ],
    }

    config = Config.model_validate(raw_config)
    assert isinstance(config.api_client, ApiClientConfig)
    assert str(config.api_client.api_url).rstrip("/") == "https://api.example.com"

    assert len(config.repositories) == 1
    repo: RepositoryConfig = config.repositories[0]
    assert repo.plugin_type == "inspire"
    assert isinstance(repo.plugin_config, InspireConfig)
    assert repo.rdi == "test-import"
    assert repo.plugin_config.csw_url == "https://csw.example.com"


def test_repository_config_source_url_inspire() -> None:
    """source_url returns the CSW URL for an INSPIRE repository."""
    repo = RepositoryConfig.model_validate({"rdi": "test", "inspire": {"csw_url": "https://csw.example.com"}})
    assert repo.source_url == "https://csw.example.com"


def test_repository_config_rejects_no_plugin() -> None:
    """RepositoryConfig must reject an entry with no plugin key set."""
    with pytest.raises(ValidationError):
        RepositoryConfig.model_validate({})


def test_repository_config_rejects_unknown_plugin() -> None:
    """RepositoryConfig must reject an entry with an unrecognised plugin key."""
    with pytest.raises(ValidationError):
        RepositoryConfig.model_validate({"unknown_plugin": {"some_field": "value"}})


def test_nice_http_client_config_defaults_to_respect_robots_txt() -> None:
    config = NiceHttpClientConfig()

    assert config.respect_robots_txt is True


# max_concurrent_http_connections is intentionally removed from the harvester core config.
# Connection limits are now configured per-plugin where supported.
