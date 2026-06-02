"""Configuration module for the Middleware Harvester core orchestrator."""

from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from middleware.api_client.config import Config as ApiClientConfig
from middleware.harvester.plugin_config import PluginConfig
from middleware.inspire.config import Config as InspireConfig
from middleware.schema_org.config import Config as SchemaOrgConfig
from middleware.shared.config.config_base import ConfigBase


class RepositoryConfig(BaseModel):
    """Configuration for an individual harvesting plugin/repository.

    Exactly one plugin key must be set per entry. The YAML format is:

        repositories:
          - inspire:
              csw_url: "https://..."
              rdi: "my-rdi"
    """

    # Plugin fields: any Optional field that holds a PluginConfig subclass.
    # No explicit list needed — the validator introspects model_fields at runtime.

    rdi: Annotated[
        str,
        Field(description="RDI identifier (e.g. inspire-import)"),
    ]
    inspire: Annotated[
        InspireConfig | None,
        Field(description="INSPIRE CSW plugin configuration"),
    ] = None
    schema_org: Annotated[
        SchemaOrgConfig | None,
        Field(description="Schema.org harvesting plugin configuration"),
    ] = None

    @model_validator(mode="after")
    def exactly_one_plugin(self) -> "RepositoryConfig":
        """Ensure exactly one plugin key is set.

        Derives the set of plugin fields dynamically from model_fields so that
        adding a new plugin only requires adding its Optional field — no separate
        registry constant needs updating.
        """
        plugin_fields = [name for name in self.__class__.model_fields if name != "rdi"]
        set_fields = [f for f in plugin_fields if getattr(self, f) is not None]
        if len(set_fields) != 1:
            raise ValueError(f"Each repository entry must have exactly one plugin key; got: {set_fields or 'none'}")
        return self

    @property
    def plugin_type(self) -> str:
        """Return the active plugin type name."""
        if self.inspire is not None:
            return "inspire"
        if self.schema_org is not None:
            return "schema_org"
        raise RuntimeError("No plugin key set — did model validation run?")  # pragma: no cover

    @property
    def plugin_config(self) -> PluginConfig:
        """Return the active plugin configuration object."""
        if self.inspire is not None:
            return self.inspire
        if self.schema_org is not None:
            return self.schema_org
        raise RuntimeError("No plugin config set — did model validation run?")  # pragma: no cover


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
