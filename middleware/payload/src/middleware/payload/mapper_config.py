"""Repository-level mapper configuration models (type-as-key)."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Annotated, Self, cast

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from middleware.payload.placeholders import PlaceholderConfig

logger = logging.getLogger(__name__)

_LEGACY_MAPPER_TYPE_MSG = (
    "mapper.type is deprecated; use type-as-key under mapper: "
    "(e.g. mapper: { regal_general: { resource_base_url: … } }). "
    "Support for mapper.type will be removed in a future release."
)

_MAPPER_TYPE_FIELDS = frozenset({
    "schema_org_general",
    "regal_general",
    "inspire_general",
    "phenoroam_general",
    "ckanext_dcat",
})

_MAPPER_TYPE_LOCAL_FIELDS: dict[str, frozenset[str]] = {
    "regal_general": frozenset({"resource_base_url"}),
    "ckanext_dcat": frozenset({"catalog_name", "catalog_url"}),
}


class MapperType(StrEnum):
    """Registered vocabulary→ARC mapper types (shared DataMapper registry keys)."""

    schema_org_general = "schema_org_general"
    regal_general = "regal_general"
    inspire_general = "inspire_general"
    phenoroam_general = "phenoroam_general"
    ckanext_dcat = "ckanext_dcat"


class MapperTypeConfig(BaseModel):
    """Base for type-named mapper config children (may be empty)."""

    model_config = ConfigDict(populate_by_name=True)


class SchemaOrgGeneralMapperConfig(MapperTypeConfig):
    """Type settings for ``schema_org_general`` (none today)."""


class RegalGeneralMapperConfig(MapperTypeConfig):
    """Type settings for ``regal_general``."""

    resource_base_url: Annotated[
        HttpUrl | None,
        Field(
            description=(
                "Optional http(s) base URL for expanding compact Regal resource ids "
                "(e.g. `frl:123`) to absolute IRIs. When unset, callers may supply a "
                "derived fallback."
            ),
        ),
    ] = None

    @field_validator("resource_base_url", mode="before")
    @classmethod
    def _blank_url_as_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class InspireGeneralMapperConfig(MapperTypeConfig):
    """Type settings for ``inspire_general`` (none today)."""


class PhenoroamGeneralMapperConfig(MapperTypeConfig):
    """Type settings for ``phenoroam_general`` (none today)."""


class CkanextDcatMapperConfig(MapperTypeConfig):
    """Type settings for ``ckanext_dcat``."""

    catalog_name: Annotated[
        str | None,
        Field(
            description=(
                "Optional display name of the source RDI's data catalog (e.g. "
                "'Smart Rural Areas Data Infrastructure (SRADI)')."
            ),
        ),
    ] = None
    catalog_url: Annotated[
        HttpUrl | None,
        Field(description="Optional http(s) URL of the source RDI's data catalog."),
    ] = None

    @field_validator("catalog_url", mode="before")
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


class MapperConfig(BaseModel):
    """Mapper selection beside the plugin key (type-as-key + shared siblings).

    Canonical form::

        mapper:
          placeholders: { … }
          regal_general:
            resource_base_url: …

    Deprecated ``{ type: …, … }`` lifts into that nested form with a warning.
    """

    model_config = ConfigDict(populate_by_name=True)

    placeholders: Annotated[
        PlaceholderConfig,
        Field(description="Placeholder text this RDI writes instead of leaving a field empty; none by default."),
    ] = PlaceholderConfig()
    schema_org_general: Annotated[
        SchemaOrgGeneralMapperConfig | None,
        Field(description="schema_org_general mapper settings."),
    ] = None
    regal_general: Annotated[
        RegalGeneralMapperConfig | None,
        Field(description="regal_general mapper settings."),
    ] = None
    inspire_general: Annotated[
        InspireGeneralMapperConfig | None,
        Field(description="inspire_general mapper settings."),
    ] = None
    phenoroam_general: Annotated[
        PhenoroamGeneralMapperConfig | None,
        Field(description="phenoroam_general mapper settings."),
    ] = None
    ckanext_dcat: Annotated[
        CkanextDcatMapperConfig | None,
        Field(description="ckanext_dcat mapper settings."),
    ] = None

    @model_validator(mode="before")
    @classmethod
    def lift_legacy_type_discriminator(cls, data: object) -> object:
        """Lift deprecated ``type:`` (+ flat type-local fields) into type-as-key."""
        if not isinstance(data, dict):
            return data
        legacy_type = data.get("type")
        if legacy_type is None:
            return data

        type_key = MapperType(legacy_type).value
        nested_present = sorted(name for name in _MAPPER_TYPE_FIELDS if data.get(name) is not None)
        if nested_present and nested_present != [type_key]:
            raise ValueError(f"mapper.type {type_key!r} conflicts with nested mapper.{', '.join(nested_present)}")

        logger.warning(_LEGACY_MAPPER_TYPE_MSG)
        lifted = {key: value for key, value in data.items() if key != "type"}
        raw_child = lifted.pop(type_key, None)
        if raw_child is None:
            child: dict[str, object] = {}
        elif isinstance(raw_child, dict):
            child = dict(raw_child)
        elif isinstance(raw_child, BaseModel):
            child = raw_child.model_dump()
        else:
            raise ValueError(f"mapper.{type_key} must be a mapping")
        for field_name in _MAPPER_TYPE_LOCAL_FIELDS.get(type_key, ()):
            if field_name in lifted:
                child[field_name] = lifted.pop(field_name)
        lifted[type_key] = child
        return lifted

    @model_validator(mode="after")
    def exactly_one_mapper_type(self) -> Self:
        """Require exactly one type-named mapper child."""
        set_fields = sorted(name for name in _MAPPER_TYPE_FIELDS if getattr(self, name) is not None)
        if len(set_fields) != 1:
            raise ValueError(
                f"mapper must set exactly one of {sorted(_MAPPER_TYPE_FIELDS)}; got: {set_fields or 'none'}"
            )
        return self

    @property
    def type(self) -> MapperType:
        """Active DataMapper registry key (single set type-named child)."""
        return MapperType(next(name for name in _MAPPER_TYPE_FIELDS if getattr(self, name) is not None))

    @property
    def type_config(self) -> MapperTypeConfig:
        """Config model for the active mapper type."""
        return cast(MapperTypeConfig, getattr(self, self.type.value))

    @property
    def resource_base_url(self) -> HttpUrl | None:
        """Regal resource base URL when active type is ``regal_general``."""
        if self.regal_general is None:
            return None
        return self.regal_general.resource_base_url

    @property
    def catalog_name(self) -> str | None:
        """Catalog display name when active type is ``ckanext_dcat``."""
        if self.ckanext_dcat is None:
            return None
        return self.ckanext_dcat.catalog_name

    @property
    def catalog_url(self) -> HttpUrl | None:
        """Catalog URL when active type is ``ckanext_dcat``."""
        if self.ckanext_dcat is None:
            return None
        return self.ckanext_dcat.catalog_url

    def normalize_resource_base_url(self) -> str | None:
        """Return a trailing-slash-normalized Regal resource base URL, or None."""
        if self.resource_base_url is None:
            return None
        return str(self.resource_base_url).rstrip("/") + "/"
