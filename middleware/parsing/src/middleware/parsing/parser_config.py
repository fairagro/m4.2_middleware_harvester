"""Repository-level parser configuration models."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from middleware.parsing.parser_type import ParserType


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
        str | None,
        Field(
            description=(
                "Optional exact http(s) IRI allowed as a remote JSON-LD ``@context`` on "
                "payloads for ``jsonld`` / ``html_jsonld``. When unset, remote context "
                "IRIs are rejected. The document (and transitive ``@import`` targets) is "
                "fetched once via polite HTTP and cached for the process lifetime. "
                "Ignored by non-JSON-LD parsers."
            ),
        ),
    ] = None

    @field_validator("allowed_context_url")
    @classmethod
    def _http_context_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if not (stripped.startswith("http://") or stripped.startswith("https://")):
            raise ValueError("allowed_context_url must be an http(s) URL")
        return stripped
