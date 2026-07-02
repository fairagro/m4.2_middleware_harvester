"""Post-fetch record filtering for Schema.org datasets."""

from __future__ import annotations

import re
from typing import Annotated, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from .jsonld_dataset import resolve_field_value
from .jsonld_types import SchemaOrgDatasetDict


class RecordFilterConfig(BaseModel):
    """Configuration for optional post-fetch Schema.org record filtering."""

    field: Annotated[
        str,
        Field(
            min_length=1,
            description=(
                "Dot-path into the extracted Schema.org Dataset JSON-LD object "
                "(e.g. publisher.name). Used to resolve the value tested by include/exclude."
            ),
        ),
    ]
    include: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Optional case-insensitive regular expression. When set, the record is kept "
                "only if the resolved field value matches. Missing values never match."
            ),
        ),
    ] = None
    exclude: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Optional case-insensitive regular expression. When set, the record is kept "
                "only if the resolved field value does not match. Missing values always pass."
            ),
        ),
    ] = None

    @field_validator("include", "exclude")
    @classmethod
    def validate_regex(cls, value: str | None) -> str | None:
        """Compile regex patterns at validation time to fail fast on typos."""
        if value is None:
            return None
        try:
            re.compile(value, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"Invalid regular expression: {exc}") from exc
        return value

    @model_validator(mode="after")
    def at_least_one_pattern(self) -> Self:
        """Require at least one of include or exclude when record_filter is set."""
        if self.include is None and self.exclude is None:
            raise ValueError("record_filter requires at least one of include or exclude")
        return self


class RecordFilter:
    """Evaluate configured include/exclude rules against a Dataset dict."""

    def __init__(self, config: RecordFilterConfig) -> None:
        """Store compiled include/exclude patterns from validated config."""
        self._field = config.field
        self._include = re.compile(config.include, re.IGNORECASE) if config.include else None
        self._exclude = re.compile(config.exclude, re.IGNORECASE) if config.exclude else None

    def evaluate(self, dataset_dict: SchemaOrgDatasetDict) -> str | None:
        """Return a skip reason when the record fails the filter, else None."""
        value = resolve_field_value(dataset_dict, self._field)
        value_display = value if value is not None else "missing"

        if self._include is not None and (value is None or not self._include.search(value)):
            return (
                f"Record filter rejected: field={self._field}, include={self._include.pattern}, value={value_display}"
            )

        if self._exclude is not None and value is not None and self._exclude.search(value):
            return (
                f"Record filter rejected: field={self._field}, exclude={self._exclude.pattern}, value={value_display}"
            )

        return None
