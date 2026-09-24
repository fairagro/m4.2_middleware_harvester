"""Unit tests for the Harvester orchestrator configuration."""

import logging

import pytest
from pydantic import ValidationError

from middleware.api_client.config import Config as ApiClientConfig
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.config import Config, RepositoryConfig
from middleware.harvester.nice_http_client import NiceHttpClientConfig
from middleware.inspire.config import Config as InspireConfig
from middleware.payload.registry import Registry


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


def _minimal_linked_data() -> dict[str, object]:
    return {
        "sitemap_url": "https://example.org/sitemap.xml",
        "sitemap_type": "xml",
        "dataset_type": "html_jsonld",
    }


def test_linked_data_repository_requires_mapper() -> None:
    with pytest.raises(ValidationError, match="mapper"):
        RepositoryConfig.model_validate({"rdi": "ld", "linked_data": _minimal_linked_data()})


def test_linked_data_repository_accepts_schema_org_mapper() -> None:
    repo = RepositoryConfig.model_validate({
        "rdi": "ld",
        "linked_data": _minimal_linked_data(),
        "mapper": {"type": "schema_org_general"},
    })
    assert repo.plugin_type == "linked_data"
    assert repo.mapper is not None
    assert repo.mapper.type == "schema_org_general"


def test_linked_data_repository_rejects_unknown_mapper_type() -> None:
    with pytest.raises(ValidationError):
        RepositoryConfig.model_validate({
            "rdi": "ld",
            "linked_data": _minimal_linked_data(),
            "mapper": {"type": "not_a_real_mapper"},
        })


def test_inspire_repository_ok_without_mapper() -> None:
    repo = RepositoryConfig.model_validate({"rdi": "inspire", "inspire": {"csw_url": "https://csw.example.com"}})
    assert repo.mapper is None
    assert repo.plugin_type == "inspire"


def test_legacy_payload_type_lifts_to_mapper(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        repo = RepositoryConfig.model_validate({
            "rdi": "ld",
            "linked_data": {**_minimal_linked_data(), "payload_type": "schema_org_general"},
        })
    assert repo.mapper is not None
    assert repo.mapper.type == "schema_org_general"
    assert repo.linked_data is not None
    assert repo.linked_data.__dict__.get("payload_type") == "schema_org_general"
    assert any("payload_type is deprecated" in record.message for record in caplog.records)


def test_legacy_payload_type_matching_mapper_still_warns(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        repo = RepositoryConfig.model_validate({
            "rdi": "ld",
            "linked_data": {**_minimal_linked_data(), "payload_type": "schema_org_general"},
            "mapper": {"type": "schema_org_general"},
        })
    assert repo.mapper is not None
    assert repo.mapper.type == "schema_org_general"
    assert any("payload_type is deprecated" in record.message for record in caplog.records)


def test_legacy_payload_type_conflicts_with_mapper() -> None:
    with pytest.raises(ValidationError, match="conflicts with mapper.type"):
        RepositoryConfig.model_validate({
            "rdi": "ld",
            "linked_data": {**_minimal_linked_data(), "payload_type": "schema_org_general"},
            "mapper": {"type": "regal_general"},
        })


def test_resource_base_url_conflict_between_linked_data_and_mapper() -> None:
    with pytest.raises(ValidationError, match="resource_base_url .* conflicts"):
        RepositoryConfig.model_validate({
            "rdi": "ld",
            "linked_data": {
                **_minimal_linked_data(),
                "sitemap_type": "regal_find",
                "dataset_type": "regal_jsonld",
                "resource_base_url": "https://a.example/resource/",
            },
            "mapper": {"type": "regal_general", "resource_base_url": "https://b.example/resource/"},
        })


def test_resource_base_url_matching_linked_data_and_mapper_ok() -> None:
    repo = RepositoryConfig.model_validate({
        "rdi": "ld",
        "linked_data": {
            **_minimal_linked_data(),
            "sitemap_type": "regal_find",
            "dataset_type": "regal_jsonld",
            "resource_base_url": "https://example.org/resource",
        },
        "mapper": {"type": "regal_general", "resource_base_url": "https://example.org/resource/"},
    })
    assert repo.mapper is not None
    assert repo.mapper.normalize_resource_base_url() == "https://example.org/resource/"


def _minimal_generic() -> dict[str, object]:
    return {
        "sitemap_url": "https://example.org/sitemap.xml",
        "protocol_type": "xml",
    }


def test_generic_repository_requires_mapper() -> None:
    with pytest.raises(ValidationError, match="mapper"):
        RepositoryConfig.model_validate({
            "rdi": "g",
            "generic": _minimal_generic(),
            "parser": {"type": "html_jsonld"},
        })


def test_generic_repository_requires_parser() -> None:
    with pytest.raises(ValidationError, match="parser"):
        RepositoryConfig.model_validate({
            "rdi": "g",
            "generic": _minimal_generic(),
            "mapper": {"type": "schema_org_general"},
        })


def test_generic_repository_accepts_schema_org_mapper() -> None:
    repo = RepositoryConfig.model_validate({
        "rdi": "g",
        "generic": _minimal_generic(),
        "parser": {"type": "html_jsonld"},
        "mapper": {"type": "schema_org_general"},
    })
    assert repo.plugin_type == "generic"
    assert repo.mapper is not None
    assert repo.mapper.type == "schema_org_general"
    assert repo.parser is not None
    assert repo.parser.type == "html_jsonld"
    assert repo.source_url == "https://example.org/sitemap.xml"


def test_generic_and_linked_data_mutual_exclusion() -> None:
    with pytest.raises(ValidationError, match="exactly one plugin key"):
        RepositoryConfig.model_validate({
            "rdi": "both",
            "generic": _minimal_generic(),
            "linked_data": _minimal_linked_data(),
            "parser": {"type": "html_jsonld"},
            "mapper": {"type": "schema_org_general"},
        })


def test_generic_unregistered_protocol_type_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enum-accepted protocol_type must still be present in Protocol.registry."""
    monkeypatch.setattr(Protocol, "registry", Registry())
    with pytest.raises(ValidationError, match="Unknown generic.protocol_type"):
        RepositoryConfig.model_validate({
            "rdi": "g",
            "generic": _minimal_generic(),
            "parser": {"type": "html_jsonld"},
            "mapper": {"type": "schema_org_general"},
        })
