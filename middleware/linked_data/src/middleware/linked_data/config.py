"""Configuration model for the Linked Data harvester plugin."""

from enum import StrEnum
from typing import Annotated
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from middleware.harvester.nice_http_client import NiceHttpClientConfig


class SitemapType(StrEnum):
    """Supported sitemap kinds for Linked Data harvesting."""

    xml = "xml"
    mycore_solr = "mycore_solr"
    regal_find = "regal_find"


class DatasetType(StrEnum):
    """Supported provider-specific dataset kinds."""

    html_jsonld = "html_jsonld"
    regal_jsonld = "regal_jsonld"


class PayloadType(StrEnum):
    """Supported dataset payload types."""

    schema_org_general = "schema_org_general"
    regal_general = "regal_general"


class Config(BaseModel):
    """Configuration model for the Linked Data harvesting plugin."""

    model_config = ConfigDict(populate_by_name=True)

    sitemap_url: Annotated[
        str,
        Field(
            description=(
                "Sitemap entry point URL. For `regal_find`, supply the `/find` base URL without query parameters."
            ),
        ),
    ]
    sitemap_type: Annotated[SitemapType, Field(description="Type of sitemap to parse.")]
    dataset_type: Annotated[DatasetType, Field(description="Provider-specific dataset kind.")]
    payload_type: Annotated[PayloadType, Field(description="Expected dataset payload type.")]
    http: Annotated[
        NiceHttpClientConfig,
        Field(
            description="HTTP client settings used by the plugin.",
            default_factory=lambda: NiceHttpClientConfig(respect_robots_txt=True),
        ),
    ]
    jsonld_parse_threshold_bytes: Annotated[
        int,
        Field(
            description="Threshold in bytes above which JSON-LD parsing is offloaded to a thread.",
            ge=1,
        ),
    ] = 65536
    page_size: Annotated[
        int,
        Field(
            description=(
                "Default page size for paginated discovery. Used as Regal `/find` "
                "`until`, and as MyCoRe Solr `rows` when `sitemap_url` has no "
                "`rows` parameter. A Solr `rows` query parameter overrides this "
                "value; Regal `until` in `sitemap_url` does not (query params on "
                "Regal URLs are ignored)."
            ),
            ge=1,
        ),
    ] = 200
    resource_base_url: Annotated[
        str | None,
        Field(
            description=(
                "Base URL for expanding compact Regal resource ids (e.g. `frl:123`) "
                "to absolute IRIs. If unset, derived as "
                "`{scheme}://{host}/resource/` from `sitemap_url`."
            ),
        ),
    ] = None
    worker_tasks: Annotated[
        int | None,
        Field(
            description=(
                "Number of worker tasks consuming discovery results. "
                "If unset, defaults to the HTTP max_connections value."
            ),
            ge=1,
        ),
    ] = None

    @property
    def effective_worker_tasks(self) -> int:
        """Return configured worker tasks or fall back to the HTTP client's max connections."""
        return self.worker_tasks or self.http.max_connections

    @property
    def effective_resource_base_url(self) -> str:
        """Return configured resource base URL or derive it from ``sitemap_url``."""
        if self.resource_base_url is not None and self.resource_base_url.strip():
            return self._normalize_resource_base_url(self.resource_base_url)
        return self._resource_base_url_from_sitemap(self.sitemap_url)

    @staticmethod
    def _normalize_resource_base_url(url: str) -> str:
        return url.rstrip("/") + "/"

    @staticmethod
    def _resource_base_url_from_sitemap(sitemap_url: str) -> str:
        parsed = urlparse(sitemap_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Cannot derive resource_base_url from sitemap URL: {sitemap_url}")
        return f"{parsed.scheme}://{parsed.netloc}/resource/"
