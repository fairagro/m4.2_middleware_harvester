"""Repository-level mapper configuration models."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class MapperType(StrEnum):
    """Registered vocabulary→ARC mapper types (shared DataMapper registry keys)."""

    schema_org_general = "schema_org_general"
    regal_general = "regal_general"
    inspire_general = "inspire_general"
    phenoroam_general = "phenoroam_general"
    ckanext_dcat = "ckanext_dcat"


class MapperConfig(BaseModel):
    """Mapper selection and mapper-specific fields beside the plugin key."""

    model_config = ConfigDict(populate_by_name=True)

    type: Annotated[MapperType, Field(description="DataMapper registry key.")]
    resource_base_url: Annotated[
        HttpUrl | None,
        Field(
            description=(
                "Optional http(s) base URL for expanding compact Regal resource ids "
                "(e.g. `frl:123`) to absolute IRIs. Used by Regal mappers; "
                "when unset, callers may supply a derived fallback."
            ),
        ),
    ] = None
    catalog_name: Annotated[
        str | None,
        Field(
            description=(
                "Optional display name of the source RDI's data catalog (e.g. "
                "'Smart Rural Areas Data Infrastructure (SRADI)'). Used by DCAT-AP "
                "mappers to record catalog provenance; kept repository-configurable "
                "so the same mapper serves any DCAT-AP RDI, not just one."
            ),
        ),
    ] = None
    catalog_url: Annotated[
        HttpUrl | None,
        Field(
            description="Optional http(s) URL of the source RDI's data catalog. Used by DCAT-AP mappers.",
        ),
    ] = None

    @field_validator("resource_base_url", "catalog_url", mode="before")
    @classmethod
    def _blank_url_as_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("catalog_name", mode="before")
    @classmethod
    def _blank_catalog_name_as_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    def normalize_resource_base_url(self) -> str | None:
        """Return a trailing-slash-normalized resource base URL, or None."""
        if self.resource_base_url is None:
            return None
        return str(self.resource_base_url).rstrip("/") + "/"
