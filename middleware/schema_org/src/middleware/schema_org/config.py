"""Configuration model for the Schema.org harvester plugin."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from middleware.harvester.nice_http_client import NiceHttpClientConfig


class SitemapType(StrEnum):
    """Supported sitemap kinds for Schema.org harvesting."""

    xml = "xml"
    mycore_solr = "mycore_solr"


class DatasetType(StrEnum):
    """Supported provider-specific dataset kinds."""

    html_jsonld = "html_jsonld"


class PayloadType(StrEnum):
    """Supported dataset payload types."""

    general = "general"
    edal = "edal"


class Config(BaseModel):
    """Configuration model for the Schema.org harvesting plugin."""

    model_config = ConfigDict(populate_by_name=True)

    sitemap_url: Annotated[str, Field(description="Sitemap entry point URL.")]
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
