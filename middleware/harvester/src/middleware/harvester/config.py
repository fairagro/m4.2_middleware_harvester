"""Configuration module for the Middleware Harvester core orchestrator."""

from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator

from middleware.api_client.config import Config as ApiClientConfig
from middleware.inspire.config import Config as InspireConfig
from middleware.linked_data.config import Config as LinkedDataConfig
from middleware.payload import (
    DataMapper,
    MapperConfig,
    PayloadKind,
)
from middleware.payload.linked_data_mapper import register_builtins as _register_builtin_mappers
from middleware.shared.config.config_base import ConfigBase

# Side effect: load Schema.org / Regal mappers into DataMapper.registry.
_ = _register_builtin_mappers

# Union of all plugin config types. Extend when adding a new plugin.
PluginConfig = InspireConfig | LinkedDataConfig

_NON_PLUGIN_FIELDS = frozenset({"rdi", "mapper"})


class RepositoryConfig(BaseModel):
    """Configuration for an individual harvesting plugin/repository.

    Exactly one plugin key must be set per entry. Shared DataMappers are
    selected via an optional sibling ``mapper:`` block (required for
    ``linked_data``).
    """

    rdi: Annotated[
        str,
        Field(description="RDI identifier (e.g. inspire-import)"),
    ]
    inspire: Annotated[
        InspireConfig | None,
        Field(description="INSPIRE CSW plugin configuration"),
    ] = None
    linked_data: Annotated[
        LinkedDataConfig | None,
        Field(description="Linked Data harvesting plugin configuration"),
    ] = None
    mapper: Annotated[
        MapperConfig | None,
        Field(description="Shared DataMapper selection (required for linked_data)."),
    ] = None

    @model_validator(mode="after")
    def exactly_one_plugin(self) -> Self:
        """Ensure exactly one plugin key is set (``mapper`` is not a plugin)."""
        all_field_names: list[str] = list(self.__class__.model_fields)
        plugin_fields = [name for name in all_field_names if name not in _NON_PLUGIN_FIELDS]
        set_fields = [f for f in plugin_fields if getattr(self, f) is not None]
        if len(set_fields) != 1:
            raise ValueError(f"Each repository entry must have exactly one plugin key; got: {set_fields or 'none'}")
        return self

    @model_validator(mode="after")
    def validate_mapper_for_linked_data(self) -> Self:
        """Require and validate ``mapper`` for linked_data repositories."""
        if self.linked_data is None:
            return self
        if self.mapper is None:
            raise ValueError("linked_data repositories require a sibling mapper: block with type")
        try:
            mapper_cls = DataMapper.registry[self.mapper.type]
        except KeyError as exc:
            raise ValueError(f"Unknown mapper.type: {self.mapper.type}") from exc
        accepts = getattr(mapper_cls, "accepts", None)
        if accepts != PayloadKind.rdf_graph:
            raise ValueError(
                f"mapper.type {self.mapper.type} accepts {accepts!r}, but linked_data produces {PayloadKind.rdf_graph}"
            )
        return self

    @property
    def plugin_type(self) -> str:
        """The active plugin type name (derived dynamically from model_fields)."""
        all_field_names: list[str] = list(self.__class__.model_fields)
        return next(f for f in all_field_names if f not in _NON_PLUGIN_FIELDS and getattr(self, f) is not None)

    @property
    def plugin_config(self) -> PluginConfig:
        """The active plugin configuration object."""
        if self.inspire is not None:
            return self.inspire
        if self.linked_data is not None:
            return self.linked_data
        raise RuntimeError("No plugin config set — did model validation run?")

    @property
    def source_url(self) -> str | None:
        """The primary entry-point URL for this plugin."""
        cfg = self.plugin_config
        return getattr(cfg, "csw_url", None) or getattr(cfg, "sitemap_url", None)


class Config(ConfigBase):
    """Configuration model for the Middleware Harvester."""

    api_client: Annotated[
        ApiClientConfig,
        Field(description="API Client configuration for FAIRAgro Middleware API"),
    ]
    repositories: Annotated[
        list[RepositoryConfig],
        Field(description="List of repositories to harvest from, mapped to plugins"),
    ]
    heartbeat_path: Annotated[
        str,
        Field(description="Path of the liveness heartbeat file touched periodically during the harvest run."),
    ] = "/tmp/harvester-live"  # noqa: S108  # nosec B108
    heartbeat_interval: Annotated[
        int,
        Field(description="Interval in seconds between heartbeat file touches.", ge=1),
    ] = 30
