"""Schema.org configuration unit tests."""

from middleware.schema_org.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType

DEFAULT_MAX_REQUESTS_PER_SECOND = 2.0


def test_config_max_requests_per_second_defaults_to_two() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )
    assert config.http.max_requests_per_second == DEFAULT_MAX_REQUESTS_PER_SECOND


def test_user_agent_string_can_be_configured() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(user_agent="CustomAgent/2.0"),
    )
    assert config.http.user_agent == "CustomAgent/2.0"


def test_user_agent_defaults_to_the_fallback_string() -> None:
    config = Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
    )
    assert config.http.user_agent == "FAIRagro-Harvester/2.0 (dataservice@fairagro.org)"
