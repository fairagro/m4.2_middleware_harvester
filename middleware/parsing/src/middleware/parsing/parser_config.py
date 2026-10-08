"""Repository-level parser configuration models (type-as-key)."""

from __future__ import annotations

import logging
from typing import Annotated, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from middleware.parsing.allowed_context import validate_allowed_context_url_value
from middleware.parsing.parser_type import ParserType

logger = logging.getLogger(__name__)

_LEGACY_PARSER_TYPE_MSG = (
    "parser.type is deprecated; use type-as-key under parser: "
    "(e.g. parser: { html_jsonld: { allowed_context_url: … } }). "
    "Support for parser.type will be removed in a future release."
)

_UNPINNED_CONTEXT_MSG = (
    "allowed_context_url is unset for a JSON-LD parser "
    "(set parser.jsonld.allowed_context_url or parser.html_jsonld.allowed_context_url). "
    "Remote @context IRIs will still be fetched and cached; pin the expected context IRI."
)

_PARSER_TYPE_FIELDS = frozenset({
    "html_jsonld",
    "rdf_xml",
    "phenoroam_xml",
    "jsonld",
})

_JSONLD_PARSER_TYPES = frozenset({ParserType.jsonld, ParserType.html_jsonld})

_PARSER_TYPE_LOCAL_FIELDS: dict[str, frozenset[str]] = {
    "html_jsonld": frozenset({"allowed_context_url", "jsonld_parse_threshold_bytes"}),
    "jsonld": frozenset({"allowed_context_url", "jsonld_parse_threshold_bytes"}),
}


class ParserTypeConfig(BaseModel):
    """Base for type-named parser config children (may be empty)."""

    model_config = ConfigDict(populate_by_name=True)


class JsonLdParserSettings(ParserTypeConfig):
    """Shared settings for JSON-LD PayloadParsers (``jsonld`` / ``html_jsonld``)."""

    allowed_context_url: Annotated[
        list[str] | None,
        Field(
            description=(
                "Optional http(s) IRI or list of IRIs pinned as allowed remote JSON-LD "
                "``@context`` values. Matching ignores trailing slashes; an ``http`` pin "
                "also accepts the same IRI under ``https``. When unset, a warning is logged "
                "at config load and absolute http(s) remotes are still fetched via polite "
                "HTTP and cached for the process."
            ),
        ),
    ] = None
    jsonld_parse_threshold_bytes: Annotated[
        int,
        Field(
            ge=1,
            description=(
                "Byte threshold above which JSON-LD parse offloads ``graph.parse`` to a "
                "worker thread. Smaller payloads parse on the event-loop thread."
            ),
        ),
    ] = 65536

    @field_validator("allowed_context_url", mode="before")
    @classmethod
    def _http_context_url(cls, value: object) -> list[str] | None:
        return validate_allowed_context_url_value(value)


class HtmlJsonldParserConfig(JsonLdParserSettings):
    """Type settings for ``html_jsonld``."""


class JsonldParserConfig(JsonLdParserSettings):
    """Type settings for ``jsonld``."""


class RdfXmlParserConfig(ParserTypeConfig):
    """Type settings for ``rdf_xml`` (none today)."""


class PhenoroamXmlParserConfig(ParserTypeConfig):
    """Type settings for ``phenoroam_xml`` (none today)."""


class ParserConfig(BaseModel):
    """Parser selection beside the plugin key (type-as-key).

    Canonical form::

        parser:
          html_jsonld:
            allowed_context_url: …

    Deprecated ``{ type: …, … }`` lifts into that nested form with a warning.
    """

    model_config = ConfigDict(populate_by_name=True)

    html_jsonld: Annotated[
        HtmlJsonldParserConfig | None,
        Field(description="html_jsonld parser settings."),
    ] = None
    jsonld: Annotated[
        JsonldParserConfig | None,
        Field(description="jsonld parser settings."),
    ] = None
    rdf_xml: Annotated[
        RdfXmlParserConfig | None,
        Field(description="rdf_xml parser settings."),
    ] = None
    phenoroam_xml: Annotated[
        PhenoroamXmlParserConfig | None,
        Field(description="phenoroam_xml parser settings."),
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

        type_key = ParserType(legacy_type).value
        nested_present = sorted(name for name in _PARSER_TYPE_FIELDS if data.get(name) is not None)
        if nested_present and nested_present != [type_key]:
            raise ValueError(f"parser.type {type_key!r} conflicts with nested parser.{', '.join(nested_present)}")

        logger.warning(_LEGACY_PARSER_TYPE_MSG)
        lifted = {key: value for key, value in data.items() if key != "type"}
        raw_child = lifted.pop(type_key, None)
        if raw_child is None:
            child: dict[str, object] = {}
        elif isinstance(raw_child, dict):
            child = dict(raw_child)
        elif isinstance(raw_child, BaseModel):
            child = raw_child.model_dump()
        else:
            raise ValueError(f"parser.{type_key} must be a mapping")
        for field_name in _PARSER_TYPE_LOCAL_FIELDS.get(type_key, ()):
            if field_name in lifted:
                child[field_name] = lifted.pop(field_name)
        lifted[type_key] = child
        return lifted

    @model_validator(mode="after")
    def exactly_one_parser_type(self) -> Self:
        """Require exactly one type-named parser child; warn if JSON-LD context unpinned."""
        set_fields = sorted(name for name in _PARSER_TYPE_FIELDS if getattr(self, name) is not None)
        if len(set_fields) != 1:
            raise ValueError(
                f"parser must set exactly one of {sorted(_PARSER_TYPE_FIELDS)}; got: {set_fields or 'none'}"
            )
        if self.type in _JSONLD_PARSER_TYPES and self.allowed_context_url is None:
            logger.warning(_UNPINNED_CONTEXT_MSG)
        return self

    @property
    def type(self) -> ParserType:
        """Active PayloadParser registry key (single set type-named child)."""
        return ParserType(next(name for name in _PARSER_TYPE_FIELDS if getattr(self, name) is not None))

    @property
    def type_config(self) -> ParserTypeConfig:
        """Config model for the active parser type."""
        return cast(ParserTypeConfig, getattr(self, self.type.value))

    @property
    def allowed_context_url(self) -> list[str] | None:
        """Allowed @context URL(s) when active type is a JSON-LD parser."""
        cfg = self.type_config
        if not isinstance(cfg, JsonLdParserSettings):
            return None
        return cfg.allowed_context_url

    @property
    def jsonld_parse_threshold_bytes(self) -> int:
        """JSON-LD parse threshold; default when active type is not JSON-LD."""
        cfg = self.type_config
        if not isinstance(cfg, JsonLdParserSettings):
            return 65536
        return cfg.jsonld_parse_threshold_bytes
