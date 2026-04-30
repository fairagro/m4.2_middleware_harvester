"""Configuration model for the Schema.org harvester plugin."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator


class SitemapType(StrEnum):
    """Supported sitemap kinds for Schema.org harvesting."""

    xml = "xml"


class DatasetType(StrEnum):
    """Supported provider-specific dataset kinds."""

    dummy = "dummy"


class PayloadType(StrEnum):
    """Supported dataset payload types."""

    dummy = "dummy"


class Config(BaseModel):
    """Configuration model for the Schema.org harvesting plugin."""

    sitemap_urls: Annotated[list[str], Field(description="List of sitemap entry points.", min_length=1)]
    sitemap_type: Annotated[SitemapType, Field(description="Type of sitemap to parse.")]
    dataset_type: Annotated[DatasetType, Field(description="Provider-specific dataset kind.")]
    payload_type: Annotated[PayloadType, Field(description="Expected dataset payload type.")]
    timeout: Annotated[int, Field(description="HTTP timeout seconds.", ge=1)] = 30

    @model_validator(mode="after")
    def validate_config(self) -> Self:
        """Validate the schema.org plugin configuration after model creation."""
        if not self.sitemap_urls:
            raise ValueError("sitemap_urls must contain at least one sitemap entry point.")
        return self
