"""Repository-level mapper configuration models."""

import logging
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from middleware.payload.placeholders import PlaceholderConfig

logger = logging.getLogger(__name__)

_LEGACY_CATALOG_FIELDS_MSG = (
    "mapper.catalog_name / mapper.catalog_url are deprecated; catalog provenance is added by the "
    "middleware API from its known_rdis registry (RDI / RDI Description / RDI URL comments). "
    "Remove these keys from the repository config; support will be removed in a future release."
)


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
                "Deprecated: catalog provenance comes from the middleware API's known_rdis. "
                "Optional display name of the source RDI's data catalog. Used by DCAT-AP "
                "mappers to record catalog provenance."
            ),
        ),
    ] = None
    catalog_url: Annotated[
        HttpUrl | None,
        Field(
            description=(
                "Deprecated: catalog provenance comes from the middleware API's known_rdis. "
                "Optional http(s) URL of the source RDI's data catalog. Used by DCAT-AP mappers."
            ),
        ),
    ] = None

    placeholders: Annotated[
        PlaceholderConfig,
        Field(description="Placeholder text this RDI writes instead of leaving a field empty; none by default."),
    ] = PlaceholderConfig()

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

    @model_validator(mode="after")
    def _warn_deprecated_catalog_fields(self) -> Self:
        """Warn when deprecated catalog provenance fields are still set (behaviour unchanged)."""
        if self.catalog_name is not None or self.catalog_url is not None:
            logger.warning(_LEGACY_CATALOG_FIELDS_MSG)
        return self

    def normalize_resource_base_url(self) -> str | None:
        """Return a trailing-slash-normalized resource base URL, or None."""
        if self.resource_base_url is None:
            return None
        return str(self.resource_base_url).rstrip("/") + "/"
