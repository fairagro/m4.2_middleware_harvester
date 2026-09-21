"""Linked Data configuration unit tests."""

from middleware.linked_data.config import Config, DatasetType, NiceHttpClientConfig, SitemapType
from middleware.payload import MapperType

DEFAULT_MAX_REQUESTS_PER_SECOND = 2.0


def test_payload_type_is_deprecated_optional_field() -> None:
    field = Config.model_fields.get("payload_type")
    assert field is not None
    assert field.deprecated is True
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=MapperType.schema_org_general,
        http=NiceHttpClientConfig(),
    )
    assert config.__dict__.get("payload_type") == MapperType.schema_org_general


def test_page_size_defaults_to_200() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        http=NiceHttpClientConfig(),
    )
    assert config.page_size == 200


def test_config_max_requests_per_second_defaults_to_two() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        http=NiceHttpClientConfig(),
    )
    assert config.http.max_requests_per_second == DEFAULT_MAX_REQUESTS_PER_SECOND


def test_user_agent_string_can_be_configured() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        http=NiceHttpClientConfig(user_agent="CustomAgent/2.0"),
    )
    assert config.http.user_agent == "CustomAgent/2.0"


def test_user_agent_defaults_to_the_fallback_string() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        http=NiceHttpClientConfig(),
    )
    assert config.http.user_agent == "FAIRagro-Harvester/2.0 (harvestmaster@fairagro.net)"


def test_resource_base_url_derived_from_sitemap_url() -> None:
    config = Config(
        sitemap_url="https://frl.publisso.de/find",
        sitemap_type=SitemapType.regal_find,
        dataset_type=DatasetType.regal_jsonld,
        http=NiceHttpClientConfig(),
    )
    assert config.effective_resource_base_url == "https://frl.publisso.de/resource/"


def test_resource_base_url_override() -> None:
    config = Config(
        sitemap_url="https://frl.publisso.de/find",
        sitemap_type=SitemapType.regal_find,
        dataset_type=DatasetType.regal_jsonld,
        resource_base_url="https://repository.publisso.de/resource",
        http=NiceHttpClientConfig(),
    )
    assert config.effective_resource_base_url == "https://repository.publisso.de/resource/"
