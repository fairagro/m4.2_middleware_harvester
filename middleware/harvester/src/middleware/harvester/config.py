"""Configuration module for the Middleware Harvester core orchestrator."""

from __future__ import annotations

import logging
from typing import Annotated, Self, cast

from pydantic import BaseModel, Field, model_validator

# Side-effect: register shared parsers + generic protocols + mappers for config validation.
import middleware.generic.protocol.xml as _register_generic_xml
import middleware.parsing.register_builtin_parsers as _register_html_jsonld_parser
from middleware.api_client.config import Config as ApiClientConfig
from middleware.generic.config import Config as GenericConfig
from middleware.generic.protocol.protocol import Protocol
from middleware.inspire.config import Config as InspireConfig
from middleware.linked_data.config import Config as LinkedDataConfig
from middleware.linked_data.plugin import LinkedDataPlugin
from middleware.oai_pmh.config import Config as OaiPmhConfig
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_config import ParserConfig
from middleware.payload import (
    DataMapper,
    MapperConfig,
)
from middleware.payload.linked_data_mapper import register_builtins as _register_builtin_mappers
from middleware.shared.config.config_base import ConfigBase

_ = (_register_html_jsonld_parser, _register_generic_xml, _register_builtin_mappers)

# Union of all plugin config types. Extend when adding a new plugin.
PluginConfig = InspireConfig | LinkedDataConfig | GenericConfig | OaiPmhConfig

_NON_PLUGIN_FIELDS = frozenset({"rdi", "mapper", "parser"})

logger = logging.getLogger(__name__)

_LEGACY_PAYLOAD_TYPE_MSG = (
    "linked_data.payload_type is deprecated; use a sibling mapper: {type: ...} block instead. "
    "Support for payload_type will be removed in a future release."
)


class RepositoryConfig(BaseModel):
    """Configuration for an individual harvesting plugin/repository.

    Exactly one plugin key must be set per entry. Shared DataMappers are
    selected via an optional sibling ``mapper:`` block (required for
    ``linked_data`` / ``generic`` / ``oai_pmh``). Shared PayloadParsers use sibling
    ``parser:`` (required for ``generic`` / ``oai_pmh``). Deprecated
    ``linked_data.payload_type`` is accepted with a ``logger.warning`` and lifted to
    ``mapper.type``.
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
    generic: Annotated[
        GenericConfig | None,
        Field(description="Generic Protocol plugin configuration"),
    ] = None
    oai_pmh: Annotated[
        OaiPmhConfig | None,
        Field(description="OAI-PMH plugin configuration"),
    ] = None
    mapper: Annotated[
        MapperConfig | None,
        Field(description="Shared DataMapper selection (required for linked_data, generic, oai_pmh)."),
    ] = None
    parser: Annotated[
        ParserConfig | None,
        Field(description="Shared PayloadParser selection (required for generic and oai_pmh)."),
    ] = None

    @model_validator(mode="after")
    def exactly_one_plugin(self) -> Self:
        """Ensure exactly one plugin key is set (``mapper`` / ``parser`` are not plugins)."""
        all_field_names: list[str] = list(self.__class__.model_fields)
        plugin_fields = [name for name in all_field_names if name not in _NON_PLUGIN_FIELDS]
        set_fields = [f for f in plugin_fields if getattr(self, f) is not None]
        if len(set_fields) != 1:
            raise ValueError(f"Each repository entry must have exactly one plugin key; got: {set_fields or 'none'}")
        return self

    @model_validator(mode="after")
    def lift_legacy_payload_type(self) -> Self:
        """Map deprecated ``linked_data.payload_type`` onto sibling ``mapper.type``."""
        if self.linked_data is None:
            return self
        # Read via __dict__ to avoid Pydantic's DeprecationWarning on field access;
        # operator-facing signal is logger.warning below.
        legacy_type = self.linked_data.__dict__.get("payload_type")
        if legacy_type is None:
            return self

        logger.warning(_LEGACY_PAYLOAD_TYPE_MSG)
        if self.mapper is None:
            return self.model_copy(update={"mapper": MapperConfig(type=legacy_type)})

        if self.mapper.type != legacy_type:
            raise ValueError(
                f"linked_data.payload_type {legacy_type!r} conflicts with mapper.type {self.mapper.type!r}"
            )
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
        produced = LinkedDataPlugin.produces
        if accepts != produced:
            raise ValueError(f"mapper.type {self.mapper.type} accepts {accepts!r}, but linked_data produces {produced}")

        # Fail closed when both blocks set an explicit base and they disagree —
        # dataset parsing uses linked_data; RegalMapper prefers mapper.
        linked_base = self.linked_data.resource_base_url
        mapper_base = self.mapper.normalize_resource_base_url()
        if linked_base is not None and linked_base.strip() and mapper_base is not None:
            normalized_linked = self.linked_data.effective_resource_base_url
            if normalized_linked != mapper_base:
                raise ValueError(
                    f"linked_data.resource_base_url {normalized_linked!r} conflicts with "
                    f"mapper.resource_base_url {mapper_base!r}"
                )
        return self

    @model_validator(mode="after")
    def validate_mapper_and_parser_for_generic(self) -> Self:
        """Require and validate ``mapper`` + ``parser`` for generic repositories."""
        if self.generic is None:
            return self
        if self.mapper is None:
            raise ValueError("generic repositories require a sibling mapper: block with type")
        if self.parser is None:
            raise ValueError("generic repositories require a sibling parser: block with type")
        try:
            mapper_cls = DataMapper.registry[self.mapper.type]
        except KeyError as exc:
            raise ValueError(f"Unknown mapper.type: {self.mapper.type}") from exc
        try:
            Protocol.registry[self.generic.protocol_type]
        except KeyError as exc:
            raise ValueError(f"Unknown generic.protocol_type: {self.generic.protocol_type}") from exc
        try:
            parser_cls = PayloadParser.registry[self.parser.type]
        except KeyError as exc:
            raise ValueError(f"Unknown parser.type: {self.parser.type}") from exc
        accepts = getattr(mapper_cls, "accepts", None)
        produced = getattr(parser_cls, "produces", None)
        if accepts != produced:
            raise ValueError(
                f"mapper.type {self.mapper.type} accepts {accepts!r}, "
                f"but parser.type {self.parser.type} produces {produced!r}"
            )

        generic_base = self.generic.resource_base_url
        mapper_base = self.mapper.normalize_resource_base_url()
        if generic_base is not None and generic_base.strip() and mapper_base is not None:
            normalized_generic = self.generic.effective_resource_base_url
            if normalized_generic != mapper_base:
                raise ValueError(
                    f"generic.resource_base_url {normalized_generic!r} conflicts with "
                    f"mapper.resource_base_url {mapper_base!r}"
                )
        return self

    @model_validator(mode="after")
    def validate_mapper_and_parser_for_oai_pmh(self) -> Self:
        """Require and validate ``mapper`` + ``parser`` for oai_pmh repositories."""
        if self.oai_pmh is None:
            return self
        if self.mapper is None:
            raise ValueError("oai_pmh repositories require a sibling mapper: block with type")
        if self.parser is None:
            raise ValueError("oai_pmh repositories require a sibling parser: block with type")
        try:
            mapper_cls = DataMapper.registry[self.mapper.type]
        except KeyError as exc:
            raise ValueError(f"Unknown mapper.type: {self.mapper.type}") from exc
        try:
            parser_cls = PayloadParser.registry[self.parser.type]
        except KeyError as exc:
            raise ValueError(f"Unknown parser.type: {self.parser.type}") from exc
        accepts = getattr(mapper_cls, "accepts", None)
        produced = getattr(parser_cls, "produces", None)
        if accepts != produced:
            raise ValueError(
                f"mapper.type {self.mapper.type} accepts {accepts!r}, "
                f"but parser.type {self.parser.type} produces {produced!r}"
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
        return cast(PluginConfig, getattr(self, self.plugin_type))

    @property
    def source_url(self) -> str | None:
        """The primary entry-point URL for this plugin."""
        cfg = self.plugin_config
        return getattr(cfg, "csw_url", None) or getattr(cfg, "sitemap_url", None) or getattr(cfg, "endpoint_url", None)


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
