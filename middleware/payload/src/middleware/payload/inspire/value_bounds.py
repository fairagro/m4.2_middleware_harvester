"""Configurable validation limits for harvested INSPIRE (ISO 19139) values.

Lives in ``middleware.payload`` beside ``InspireRecord`` because the models read these
limits from the validation context; protocol plugins (``middleware.inspire``) expose them
via their config.
"""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class ValueBounds(BaseModel):
    """Validation limits applied to every harvested CSW/ISO-19139 value.

    A record whose values exceed these limits fails validation (``InspireRecord``) and is
    reported as a failed record — values are never truncated or dropped.
    """

    max_str_short: Annotated[
        int,
        Field(description="Maximum length of short code/label fields (edition, version, protocol, phone).", ge=1),
    ] = 200
    max_str_medium: Annotated[
        int,
        Field(
            description=(
                "Maximum length of single-line fields: identifiers, titles, list-element strings, "
                "contact fields and URLs."
            ),
            ge=1,
        ),
    ] = 1_000
    max_str_long: Annotated[
        int,
        Field(description="Maximum length of paragraph fields: abstract, lineage, purpose, descriptions.", ge=1),
    ] = 10_000
    max_list_items: Annotated[
        int,
        Field(description="Maximum number of items in any list field of a record.", ge=1),
    ] = 500
    allowed_url_schemes: Annotated[
        frozenset[str],
        Field(
            description=(
                "URL schemes accepted in harvested URL fields. The harvester never dereferences these "
                "URLs; they are copied into the ARC, so this is a security policy (rejects e.g. "
                "javascript:, data:, file:)."
            ),
            min_length=1,
        ),
    ] = frozenset({"http", "https", "ftp"})

    @field_validator("allowed_url_schemes")
    @classmethod
    def _lowercase_schemes(cls, v: frozenset[str]) -> frozenset[str]:
        return frozenset(s.lower() for s in v)
