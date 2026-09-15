"""Repository-level mapper configuration models."""

from enum import StrEnum
from typing import Annotated
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field


class MapperType(StrEnum):
    """Registered vocabulary→ARC mapper types (shared DataMapper registry keys)."""

    schema_org_general = "schema_org_general"
    regal_general = "regal_general"


class MapperConfig(BaseModel):
    """Mapper selection and mapper-specific fields beside the plugin key."""

    model_config = ConfigDict(populate_by_name=True)

    type: Annotated[MapperType, Field(description="DataMapper registry key.")]
    resource_base_url: Annotated[
        str | None,
        Field(
            description=(
                "Optional base URL for expanding compact Regal resource ids "
                "(e.g. `frl:123`) to absolute IRIs. Used by Regal mappers; "
                "when unset, callers may supply a derived fallback."
            ),
        ),
    ] = None

    def normalize_resource_base_url(self) -> str | None:
        """Return a trailing-slash-normalized resource base URL, or None."""
        if self.resource_base_url is None or not self.resource_base_url.strip():
            return None
        return self.resource_base_url.rstrip("/") + "/"

    @staticmethod
    def resource_base_url_from_sitemap(sitemap_url: str) -> str:
        """Derive ``{scheme}://{host}/resource/`` from a sitemap entry URL."""
        parsed = urlparse(sitemap_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Cannot derive resource_base_url from sitemap URL: {sitemap_url}")
        return f"{parsed.scheme}://{parsed.netloc}/resource/"
