"""Repository-level parser configuration models."""

from __future__ import annotations

import logging
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from middleware.parsing.allowed_context import validate_allowed_context_url_value
from middleware.parsing.parser_type import ParserType

logger = logging.getLogger(__name__)

_JSONLD_PARSER_TYPES = frozenset({ParserType.jsonld, ParserType.html_jsonld})
_UNPINNED_CONTEXT_MSG = (
    "parser.allowed_context_url is unset for a JSON-LD parser. "
    "Remote @context IRIs will still be fetched and cached; set allowed_context_url "
    "to the exact IRI used by the source to pin the expected context."
)


class ParserConfig(BaseModel):
    """Parser selection beside the plugin key (shared PayloadParser registry)."""

    model_config = ConfigDict(populate_by_name=True)

    type: Annotated[ParserType, Field(description="PayloadParser registry key.")]
    jsonld_parse_threshold_bytes: Annotated[
        int,
        Field(
            description=(
                "Byte threshold above which JSON-LD PayloadParsers (``jsonld``, "
                "``html_jsonld``) offload ``graph.parse`` to a worker thread. "
                "Ignored by parsers that do not parse JSON-LD."
            ),
            ge=1,
        ),
    ] = 65536
    allowed_context_url: Annotated[
        list[str] | None,
        Field(
            description=(
                "Optional http(s) IRI or list of IRIs pinned as allowed remote JSON-LD "
                "``@context`` values for ``jsonld`` / ``html_jsonld``. Matching ignores "
                "trailing slashes; an ``http`` pin also accepts the same IRI under "
                "``https``. When unset on a JSON-LD parser, a warning is logged "
                "at config load and absolute http(s) remotes are still fetched via polite "
                "HTTP and cached for the process. Ignored by non-JSON-LD parsers."
            ),
        ),
    ] = None

    @field_validator("allowed_context_url", mode="before")
    @classmethod
    def _http_context_url(cls, value: object) -> list[str] | None:
        return validate_allowed_context_url_value(value)

    @model_validator(mode="after")
    def warn_unpinned_jsonld_context(self) -> Self:
        """Warn when JSON-LD parsers omit ``allowed_context_url`` (legacy-compatible)."""
        if self.type in _JSONLD_PARSER_TYPES and self.allowed_context_url is None:
            logger.warning(_UNPINNED_CONTEXT_MSG)
        return self
