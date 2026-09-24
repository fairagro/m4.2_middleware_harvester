"""Configuration model for the generic harvest plugin."""

from enum import StrEnum
from typing import Annotated
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from middleware.harvester.nice_http_client import NiceHttpClientConfig


class ProtocolType(StrEnum):
    """Registered Protocol kinds for generic harvesting."""

    xml = "xml"


class Config(BaseModel):
    """Configuration for the generic Protocol + shared PayloadParser plugin.

    Shared parser selection uses the repository-level ``parser:`` block.
    """

    model_config = ConfigDict(populate_by_name=True)

    protocol_type: Annotated[ProtocolType, Field(description="Registered Protocol implementation key.")]
    sitemap_url: Annotated[
        str,
        Field(
            description=(
                "Protocol entry-point URL (XML sitemap, Solr select, Regal /find, …). "
                "Field name retained for compatibility with linked_data configs."
            ),
        ),
    ]
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
            description="Default page size for paginated discovery protocols.",
            ge=1,
        ),
    ] = 200
    resource_base_url: Annotated[
        str | None,
        Field(
            description=(
                "Optional base URL for expanding compact resource ids. "
                "If unset, derived as `{scheme}://{host}/resource/` from `sitemap_url`."
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
        """Configured worker tasks or fall back to the HTTP client's max connections."""
        return self.worker_tasks or self.http.max_connections

    @property
    def effective_resource_base_url(self) -> str:
        """Configured resource base URL or derive it from ``sitemap_url``."""
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
