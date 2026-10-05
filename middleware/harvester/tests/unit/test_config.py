"""Unit tests for the Harvester orchestrator configuration."""

import logging

import pytest
from pydantic import ValidationError

from middleware.api_client.config import Config as ApiClientConfig
from middleware.generic.protocol.protocol import Protocol
from middleware.harvester.config import Config, RepositoryConfig
from middleware.harvester.nice_http_client import NiceHttpClientConfig
from middleware.inspire.config import Config as InspireConfig
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
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
                "mapper": {"type": "inspire_general"},
            }
        ],
    }

    config = Config.model_validate(raw_config)
    assert isinstance(config.api_client, ApiClientConfig)
    assert str(config.api_client.api_url).rstrip("/") == "https://api.example.com"
    assert config.jsonld_context_cache_max_entries == 64

    assert len(config.repositories) == 1
    repo: RepositoryConfig = config.repositories[0]
    assert repo.plugin_type == "inspire"
    assert isinstance(repo.plugin_config, InspireConfig)
    assert repo.rdi == "test-import"
    assert repo.plugin_config.csw_url == "https://csw.example.com"


def test_jsonld_context_cache_max_entries_accepts_override() -> None:
    config = Config.model_validate({
        "api_client": {"api_url": "https://api.example.com"},
        "repositories": [
            {"rdi": "test", "inspire": {"csw_url": "https://csw.example.com"}, "mapper": {"type": "inspire_general"}},
        ],
        "jsonld_context_cache_max_entries": 8,
    })
    assert config.jsonld_context_cache_max_entries == 8


def test_jsonld_context_cache_max_entries_rejects_non_positive() -> None:
    with pytest.raises(ValidationError):
        Config.model_validate({
            "api_client": {"api_url": "https://api.example.com"},
            "repositories": [
                {
                    "rdi": "test",
                    "inspire": {"csw_url": "https://csw.example.com"},
                    "mapper": {"type": "inspire_general"},
                },
            ],
            "jsonld_context_cache_max_entries": 0,
        })


def test_repository_config_source_url_inspire() -> None:
    """source_url returns the CSW URL for an INSPIRE repository."""
    repo = RepositoryConfig.model_validate({
        "rdi": "test",
        "inspire": {"csw_url": "https://csw.example.com"},
        "mapper": {"type": "inspire_general"},
    })
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


def test_inspire_repository_omitted_mapper_defaults_to_inspire_general(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        repo = RepositoryConfig.model_validate({"rdi": "inspire", "inspire": {"csw_url": "https://csw.example.com"}})
    assert repo.mapper is not None
    assert repo.mapper.type == "inspire_general"
    assert any("inspire without a sibling mapper: block is deprecated" in record.message for record in caplog.records)


def test_inspire_repository_accepts_inspire_general() -> None:
    repo = RepositoryConfig.model_validate({
        "rdi": "inspire",
        "inspire": {"csw_url": "https://csw.example.com"},
        "mapper": {"type": "inspire_general"},
    })
    assert repo.mapper is not None
    assert repo.mapper.type == "inspire_general"
    assert repo.plugin_type == "inspire"


def test_inspire_repository_rejects_rdf_mapper() -> None:
    with pytest.raises(ValidationError, match="inspire_record"):
        RepositoryConfig.model_validate({
            "rdi": "inspire",
            "inspire": {"csw_url": "https://csw.example.com"},
            "mapper": {"type": "schema_org_general"},
        })


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


def test_linked_data_mycore_solr_emits_deprecation_warning(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        repo = RepositoryConfig.model_validate({
            "rdi": "ld",
            "linked_data": {
                **_minimal_linked_data(),
                "sitemap_url": "https://example.org/servlets/solr/select",
                "sitemap_type": "mycore_solr",
            },
            "mapper": {"type": "schema_org_general"},
        })
    assert repo.linked_data is not None
    assert repo.linked_data.sitemap_type.value == "mycore_solr"
    assert any("sitemap_type: mycore_solr is deprecated" in record.message for record in caplog.records)
    assert any("generic.protocol.mycore_solr" in record.message for record in caplog.records)


def test_linked_data_other_sitemap_types_skip_mycore_deprecation(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        RepositoryConfig.model_validate({
            "rdi": "ld-xml",
            "linked_data": _minimal_linked_data(),
            "mapper": {"type": "schema_org_general"},
        })
        RepositoryConfig.model_validate({
            "rdi": "ld-regal",
            "linked_data": {
                **_minimal_linked_data(),
                "sitemap_type": "regal_find",
                "dataset_type": "regal_jsonld",
            },
            "mapper": {"type": "regal_general"},
        })
    assert not any("sitemap_type: mycore_solr is deprecated" in record.message for record in caplog.records)


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
    with pytest.raises(ValidationError, match="Unknown generic.protocol type"):
        RepositoryConfig.model_validate({
            "rdi": "g",
            "generic": _minimal_generic(),
            "parser": {"type": "html_jsonld"},
            "mapper": {"type": "schema_org_general"},
        })


def test_generic_nested_protocol_source_url() -> None:
    repo = RepositoryConfig.model_validate({
        "rdi": "g",
        "generic": {
            "protocol": {
                "mycore_solr": {
                    "entry_url": "https://example.org/servlets/solr/select",
                    "page_size": 10,
                }
            }
        },
        "parser": {"type": "html_jsonld"},
        "mapper": {"type": "schema_org_general"},
    })
    assert repo.source_url == "https://example.org/servlets/solr/select"
    assert repo.generic is not None
    assert repo.generic.active_protocol_type.value == "mycore_solr"


def _minimal_oai_pmh() -> dict[str, object]:
    return {
        "endpoint_url": "https://example.org/oai",
        "metadata_prefix": "rdf",
    }


def test_oai_pmh_repository_requires_mapper() -> None:
    with pytest.raises(ValidationError, match="mapper"):
        RepositoryConfig.model_validate({
            "rdi": "oai",
            "oai_pmh": _minimal_oai_pmh(),
            "parser": {"type": "rdf_xml"},
        })


def test_oai_pmh_repository_requires_parser() -> None:
    with pytest.raises(ValidationError, match="parser"):
        RepositoryConfig.model_validate({
            "rdi": "oai",
            "oai_pmh": _minimal_oai_pmh(),
            "mapper": {"type": "schema_org_general"},
        })


def test_oai_pmh_repository_accepts_parser_and_mapper() -> None:
    repo = RepositoryConfig.model_validate({
        "rdi": "oai",
        "oai_pmh": _minimal_oai_pmh(),
        "parser": {"type": "rdf_xml"},
        "mapper": {"type": "schema_org_general"},
    })
    assert repo.plugin_type == "oai_pmh"
    assert repo.parser is not None
    assert repo.parser.type == "rdf_xml"
    assert repo.mapper is not None
    assert repo.source_url == "https://example.org/oai"


def test_oai_pmh_repository_rejects_kind_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Startup kind alignment must fail when parser.produces != mapper.accepts."""
    parser_cls = PayloadParser.registry[ParserType.rdf_xml]
    monkeypatch.setattr(parser_cls, "produces", "not-rdf-graph")
    with pytest.raises(ValidationError, match="accepts"):
        RepositoryConfig.model_validate({
            "rdi": "oai",
            "oai_pmh": _minimal_oai_pmh(),
            "parser": {"type": "rdf_xml"},
            "mapper": {"type": "schema_org_general"},
        })


def test_oai_pmh_and_generic_mutual_exclusion() -> None:
    with pytest.raises(ValidationError, match="exactly one plugin key"):
        RepositoryConfig.model_validate({
            "rdi": "both",
            "oai_pmh": _minimal_oai_pmh(),
            "generic": _minimal_generic(),
            "parser": {"type": "rdf_xml"},
            "mapper": {"type": "schema_org_general"},
        })
