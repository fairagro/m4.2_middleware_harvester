"""Configuration module for the Middleware Harvester core orchestrator."""

from __future__ import annotations

import logging
from typing import Annotated, Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Side-effect: register shared parsers + generic protocols + mappers for config validation.
import middleware.generic.protocol.dcat_ap as _register_generic_dcat_ap
import middleware.generic.protocol.mycore_rest as _register_generic_mycore_rest
import middleware.generic.protocol.mycore_solr as _register_generic_mycore_solr
import middleware.generic.protocol.pubplant_json_array as _register_generic_pubplant_json_array
import middleware.generic.protocol.regal_find as _register_generic_regal_find
import middleware.generic.protocol.xml as _register_generic_xml
import middleware.parsing.register_builtin_parsers as _register_builtin_parsers
from middleware.api_client.config import Config as ApiClientConfig
from middleware.generic.config import Config as GenericConfig
from middleware.generic.protocol.protocol import Protocol
from middleware.inspire.config import Config as InspireConfig
from middleware.inspire.plugin import InspirePlugin
from middleware.oai_pmh.config import Config as OaiPmhConfig
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_config import ParserConfig
from middleware.payload import (
    DataMapper,
    MapperConfig,
    register_builtin_mappers as _register_builtin_mappers,
)
from middleware.shared.config.config_base import ConfigBase

_ = (
    _register_builtin_parsers,
    _register_generic_xml,
    _register_generic_mycore_solr,
    _register_generic_mycore_rest,
    _register_generic_dcat_ap,
    _register_generic_pubplant_json_array,
    _register_generic_regal_find,
    _register_builtin_mappers,
)

# Union of all plugin config types. Extend when adding a new plugin.
PluginConfig = InspireConfig | GenericConfig | OaiPmhConfig

_NON_PLUGIN_FIELDS = frozenset({"rdi", "mapper", "parser"})

logger = logging.getLogger(__name__)

_LEGACY_INSPIRE_MAPPER_MSG = (
    "inspire without a sibling mapper: block is deprecated; "
    "add mapper: { inspire_general: {} }. "
    "Omitting mapper will be rejected in a future release."
)


class RepositoryConfig(BaseModel):
    """Configuration for an individual harvesting plugin/repository.

    Exactly one plugin key must be set per entry (``inspire``, ``generic``, or
    ``oai_pmh``). Shared DataMappers are selected via a sibling ``mapper:`` block
    (always required after validation). Omitted ``mapper`` is still accepted for
    the deprecated ``inspire`` → ``inspire_general`` lift with a ``logger.warning``.
    Shared PayloadParsers use sibling ``parser:`` (required for ``generic`` /
    ``oai_pmh``). Unknown repository keys are rejected (``extra="forbid"``).
    """

    model_config = ConfigDict(extra="forbid")

    rdi: Annotated[
        str,
        Field(description="RDI identifier (e.g. inspire-import)"),
    ]
    inspire: Annotated[
        InspireConfig | None,
        Field(description="INSPIRE CSW plugin configuration"),
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
        MapperConfig,
        Field(description="Shared DataMapper selection (type-as-key; required for every repository)."),
    ]
    parser: Annotated[
        ParserConfig | None,
        Field(description="Shared PayloadParser selection (required for generic and oai_pmh)."),
    ] = None

    @model_validator(mode="before")
    @classmethod
    def lift_omitted_mapper(cls, data: object) -> object:
        """Inject deprecated inspire omit→mapper lift so ``mapper`` is always present for validation."""
        if not isinstance(data, dict):
            return data
        lifted = dict(data)
        if lifted.get("mapper") is not None:
            return lifted
        if lifted.get("inspire") is not None:
            logger.warning(_LEGACY_INSPIRE_MAPPER_MSG)
            lifted["mapper"] = {"inspire_general": {}}
        return lifted

    @model_validator(mode="after")
    def exactly_one_plugin(self) -> Self:
        """Ensure exactly one plugin key is set (``mapper`` / ``parser`` are not plugins)."""
        plugin_fields = [name for name, _ in type(self).model_fields.items() if name not in _NON_PLUGIN_FIELDS]
        set_fields = [name for name in plugin_fields if getattr(self, name) is not None]
        if len(set_fields) != 1:
            raise ValueError(f"Each repository entry must have exactly one plugin key; got: {set_fields or 'none'}")
        return self

    @model_validator(mode="after")
    def validate_mapper_and_parser_for_generic(self) -> Self:
        """Validate ``mapper`` + require ``parser`` for generic repositories."""
        if self.generic is None:
            return self
        if self.parser is None:
            raise ValueError(
                "generic repositories require a sibling type-as-key parser: block (e.g. parser: { html_jsonld: {} })"
            )
        try:
            mapper_cls = DataMapper.registry[self.mapper.type]
        except KeyError as exc:
            raise ValueError(f"Unknown mapper.type: {self.mapper.type}") from exc
        try:
            Protocol.registry[self.generic.active_protocol_type]
        except KeyError as exc:
            raise ValueError(f"Unknown generic.protocol type: {self.generic.active_protocol_type}") from exc
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
        """Validate ``mapper`` + require ``parser`` for oai_pmh repositories."""
        if self.oai_pmh is None:
            return self
        if self.parser is None:
            raise ValueError(
                "oai_pmh repositories require a sibling type-as-key parser: block (e.g. parser: { phenoroam_xml: {} })"
            )
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

    @model_validator(mode="after")
    def validate_mapper_for_inspire(self) -> Self:
        """Validate ``mapper`` for inspire repositories (after optional default lift)."""
        if self.inspire is None:
            return self
        try:
            mapper_cls = DataMapper.registry[self.mapper.type]
        except KeyError as exc:
            raise ValueError(f"Unknown mapper.type: {self.mapper.type}") from exc
        accepts = getattr(mapper_cls, "accepts", None)
        produced = InspirePlugin.produces
        if accepts != produced:
            raise ValueError(f"mapper.type {self.mapper.type} accepts {accepts!r}, but inspire produces {produced!r}")
        return self

    @property
    def plugin_type(self) -> str:
        """The active plugin type name (derived dynamically from model_fields)."""
        return next(
            name
            for name, _ in type(self).model_fields.items()
            if name not in _NON_PLUGIN_FIELDS and getattr(self, name) is not None
        )

    @property
    def plugin_config(self) -> PluginConfig:
        """The active plugin configuration object."""
        return cast(PluginConfig, getattr(self, self.plugin_type))

    @property
    def source_url(self) -> str | None:
        """The primary entry-point URL for this plugin, when the config exposes one."""
        cfg = self.plugin_config
        if self.generic is not None:
            entry_url = getattr(self.generic.effective_protocol.type_config, "entry_url", None)
            return entry_url if isinstance(entry_url, str) else None
        return getattr(cfg, "csw_url", None) or getattr(cfg, "endpoint_url", None)


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
    jsonld_context_cache_max_entries: Annotated[
        int,
        Field(
            description=(
                "Maximum number of remote JSON-LD context documents retained in the "
                "process-lifetime shared cache (LRU eviction when full). Applies to "
                "``jsonld`` / ``html_jsonld`` parsers."
            ),
            ge=1,
        ),
    ] = 64
