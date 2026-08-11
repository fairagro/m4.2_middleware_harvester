"""Configuration module for the Inspire to ARC middleware."""

from typing import Annotated, Self

from pydantic import BaseModel, Field, field_validator, model_validator


class Config(BaseModel):
    """Configuration model for the Inspire to ARC middleware."""

    model_config = {
        "populate_by_name": True,
    }

    csw_url: Annotated[str, Field(description="URL of the CSW endpoint")]
    cql_query: Annotated[
        str | None,
        Field(alias="query", description="CQL filter string, e.g. \"AnyText LIKE '%agriculture%'\""),
    ] = None
    xml_query: Annotated[
        str | None,
        Field(
            alias="xml_request",
            description=(
                "Raw GetRecords XML body (overrides cql_query). Paginated: filter preserved; "
                "startPosition/maxRecords rewritten per page. XML maxRecords overrides chunk_size; "
                "XML startPosition overrides the initial offset. Use config max_records to cap total."
            ),
        ),
    ] = None
    chunk_size: Annotated[
        int,
        Field(
            description=(
                "Number of records to fetch per paginated CSW request. "
                "For xml_query, a valid GetRecords maxRecords attribute overrides this page size."
            ),
            ge=1,
        ),
    ] = 50

    max_records: Annotated[
        int | None,
        Field(
            description=(
                "Maximum number of records to harvest across all pages (None = all records). "
                "Debug/test limit for every query mode; not the CSW per-request maxRecords page size."
            ),
        ),
    ] = None

    timeout: Annotated[
        int,
        Field(description="CSW connection timeout in seconds.", ge=1),
    ] = 30

    csw_thread_pool_size: Annotated[
        int,
        Field(
            description="Maximum number of worker threads used for blocking CSW calls.",
            ge=1,
        ),
    ] = 4

    user_agent: Annotated[
        str,
        Field(description="User-Agent header value used for CSW requests."),
    ] = "FAIRagro-Harvester/2.0 (harvestmaster@fairagro.net)"

    verify_ssl: Annotated[
        bool | str,
        Field(
            description=(
                "TLS certificate verification for CSW/OWSLib requests. "
                "True uses the system CA store; False disables verification; "
                "a string is a path to a CA bundle (passed through to OWSLib). "
                "Independent of harvester API verify_ssl."
            ),
        ),
    ] = True

    @field_validator("verify_ssl", mode="before")
    @classmethod
    def coerce_verify_ssl_bool_strings(cls, v: object) -> object:
        """Treat boolean-like strings as bool so quoted YAML/env values disable correctly.

        Pydantic keeps ``"false"`` / ``"true"`` as ``str`` under ``bool | str``, which
        would otherwise be forwarded to OWSLib as a CA bundle path.
        """
        if isinstance(v, str):
            lowered = v.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off"}:
                return False
        return v

    @field_validator("user_agent")
    @classmethod
    def user_agent_must_be_single_line(cls, v: str) -> str:
        """Reject user-agent strings containing CR or LF to prevent HTTP header injection."""
        if "\r" in v or "\n" in v:
            raise ValueError("user_agent must not contain CR (\\r) or LF (\\n) characters")
        return v

    retry_attempts: Annotated[
        int,
        Field(
            description="Number of additional retry attempts for transient CSW connection failures.",
            ge=0,
        ),
    ] = 5
    retry_backoff_base: Annotated[
        float,
        Field(
            description="Base delay in seconds for CSW retry backoff.",
            gt=0,
        ),
    ] = 1.0
    retry_backoff_factor: Annotated[
        float,
        Field(
            description="Exponential backoff factor for CSW retry delays.",
            ge=1,
        ),
    ] = 2.0
    retry_max_delay: Annotated[
        float,
        Field(
            description="Maximum delay in seconds for CSW retry backoff.",
            ge=0,
        ),
    ] = 600.0

    @model_validator(mode="after")
    def _check_mutually_exclusive_filters(self) -> Self:
        """Ensure at most one of cql_query and xml_query is set."""
        if self.cql_query is not None and self.xml_query is not None:
            raise ValueError(
                "Config conflict: cql_query and xml_query are mutually exclusive. Provide at most one of them."
            )
        return self
