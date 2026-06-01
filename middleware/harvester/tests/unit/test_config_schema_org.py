"""Config validation tests for schema_org plugin with EDAL-PGP payload type."""

from middleware.harvester.nice_http_client import NiceHttpClientConfig
from middleware.schema_org.config import Config as SchemaOrgConfig, DatasetType, PayloadType, SitemapType
from middleware.schema_org.plugin import SchemaOrgPlugin
from middleware.schema_org.schema_org_mapper.edal_pgp import EdalPgpMapper


def _make_schema_org_config(payload_type: PayloadType = PayloadType.edal_pgp) -> SchemaOrgConfig:
    return SchemaOrgConfig(
        sitemap_url="https://example.com/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=payload_type,
        http=NiceHttpClientConfig(),
    )


def test_repository_config_with_schema_org_edal_pgp_validates() -> None:
    from middleware.harvester.config import RepositoryConfig

    config = _make_schema_org_config(PayloadType.edal_pgp)
    repo = RepositoryConfig(rdi="edal-pgp-test", schema_org=config)
    assert repo.rdi == "edal-pgp-test"
    assert repo.schema_org is not None
    assert repo.inspire is None


def test_repository_config_with_schema_org_returns_schema_org_config() -> None:
    from middleware.harvester.config import RepositoryConfig

    config = _make_schema_org_config(PayloadType.edal_pgp)
    repo = RepositoryConfig(rdi="edal-pgp-test", schema_org=config)
    plugin_cfg = repo.plugin_config
    assert plugin_cfg is config
    from middleware.harvester.plugin_config import PluginConfig

    assert isinstance(plugin_cfg, PluginConfig)


def test_schema_org_config_with_payload_type_edal_pgp_instantiates() -> None:
    config = _make_schema_org_config(PayloadType.edal_pgp)
    assert config.payload_type == PayloadType.edal_pgp
    assert config.sitemap_url == "https://example.com/sitemap.xml"


def test_create_mapper_dispatches_to_edal_pgp_mapper() -> None:
    config = _make_schema_org_config(PayloadType.edal_pgp)
    mapper = SchemaOrgPlugin.create_mapper(config)
    assert isinstance(mapper, EdalPgpMapper)
