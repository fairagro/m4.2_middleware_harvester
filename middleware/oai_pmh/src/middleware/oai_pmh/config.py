"""Configuration model for the OAI-PMH harvest plugin."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class Config(BaseModel):
    """Configuration for the OAI-PMH plugin (shared parser via sibling ``parser:``)."""

    model_config = ConfigDict(populate_by_name=True)

    endpoint_url: Annotated[
        str,
        Field(description="OAI-PMH base endpoint URL (verb requests are issued against this URL)."),
    ]
    metadata_prefix: Annotated[
        str,
        Field(description="OAI metadataPrefix used for ListRecords (e.g. rdf, oai_dc)."),
    ]
    sets: Annotated[
        list[str],
        Field(
            description=(
                "Optional OAI setSpec values. Empty list = one unfiltered ListRecords; "
                "non-empty = one ListRecords pass per setSpec in order."
            ),
            default_factory=list,
        ),
    ]
    user_agent: Annotated[
        str,
        Field(description="User-Agent sent on OAI HTTP requests."),
    ] = "FAIRagro-Middleware-Harvester/oai-pmh"
    timeout: Annotated[
        float,
        Field(description="HTTP request timeout in seconds for OAI calls.", gt=0),
    ] = 60.0
    max_retries: Annotated[
        int,
        Field(description="Maximum retries for transient OAI HTTP failures.", ge=0),
    ] = 5
    retry_status_codes: Annotated[
        tuple[int, ...],
        Field(description="HTTP status codes that trigger retries."),
    ] = (503,)
    default_retry_after: Annotated[
        float,
        Field(description="Fallback Retry-After seconds when the response omits the header.", ge=0),
    ] = 60.0
    retry_on_transport_error: Annotated[
        bool,
        Field(description="Whether to retry on transport-level errors."),
    ] = True
    initial_backoff: Annotated[
        float,
        Field(description="Initial backoff seconds for retry delays.", gt=0),
    ] = 1.0
    respect_robots_txt: Annotated[
        bool,
        Field(description="When true, fail closed if robots.txt disallows the OAI endpoint."),
    ] = True
    max_requests_per_second: Annotated[
        float | None,
        Field(
            description="Optional per-host request rate limit applied around Scythe calls.",
            gt=0,
        ),
    ] = None
