"""Configurable validation limits for harvested INSPIRE (ISO 19139) values.

Lives in ``middleware.payload`` beside ``InspireRecord`` because the models read these
limits from the validation context; protocol plugins (``middleware.inspire``) expose them
via their config.
"""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from middleware.payload.placeholders import DEFAULT_PLACEHOLDER_VALUES, normalize_placeholder_values


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
    placeholder_values: Annotated[
        frozenset[str],
        Field(
            description=(
                "Whole-value placeholders (case-insensitive) treated as absent in optional fields, "
                "e.g. 'None', 'No information provided'. Unrendered $var / {{var}} templates always "
                "count. Required fields (identifier, title, abstract) are not affected."
            ),
        ),
    ] = DEFAULT_PLACEHOLDER_VALUES

    @field_validator("allowed_url_schemes")
    @classmethod
    def _lowercase_schemes(cls, v: frozenset[str]) -> frozenset[str]:
        return frozenset(s.lower() for s in v)

    @field_validator("placeholder_values")
    @classmethod
    def _fold_placeholders(cls, v: frozenset[str]) -> frozenset[str]:
        return normalize_placeholder_values(v)
