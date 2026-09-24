"""Repository-level parser configuration models."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from middleware.parsing.parser_type import ParserType


class ParserConfig(BaseModel):
    """Parser selection beside the plugin key (shared PayloadParser registry)."""

    model_config = ConfigDict(populate_by_name=True)

    type: Annotated[ParserType, Field(description="PayloadParser registry key.")]
