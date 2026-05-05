"""Configuration model for the Schema.org harvester plugin."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


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


class Config(BaseModel):
    """Configuration model for the Schema.org harvesting plugin."""

    sitemap_url: Annotated[str, Field(description="Sitemap entry point URL.")]
    sitemap_type: Annotated[SitemapType, Field(description="Type of sitemap to parse.")]
    dataset_type: Annotated[DatasetType, Field(description="Provider-specific dataset kind.")]
    payload_type: Annotated[PayloadType, Field(description="Expected dataset payload type.")]
    timeout: Annotated[int, Field(description="HTTP timeout seconds.", ge=1)] = 30
    max_connections: Annotated[
        int,
        Field(
            description="Maximum number of concurrent HTTP connections used for sitemap downloads.",
            ge=1,
        ),
    ] = 10
