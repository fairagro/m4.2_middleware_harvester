"""Configuration module for the Schema.org to ARC middleware."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, model_validator


class Config(BaseModel):
    """Configuration model for the Schema.org to ARC middleware."""

    json_source_url: Annotated[
        str,
        Field(description="URL or path to the Schema.org JSON source"),
    ]
    json_source_type: Annotated[
        Literal["url", "file", "directory"],
        Field(
            description=("Type of JSON source: 'url' for HTTP endpoint, 'file' for local file, 'directory' for folder")
        ),
    ] = "url"
    source_identifier: Annotated[
        str | None,
        Field(description="Optional identifier to filter sources (e.g., provider name like 'edal', 'bonares')"),
    ] = None
    timeout: Annotated[
        int,
        Field(description="Request timeout in seconds.", ge=1),
    ] = 30
    batch_size: Annotated[
        int,
        Field(description="Number of records to process per batch.", ge=1),
    ] = 50

    @model_validator(mode="after")
    def _validate_source_config(self) -> Self:
        """Validate source configuration based on source type."""
        if self.json_source_type == "url" and not self.json_source_url.startswith(("http://", "https://")):
            raise ValueError("json_source_url must be a valid HTTP/HTTPS URL when json_source_type is 'url'")
        return self
