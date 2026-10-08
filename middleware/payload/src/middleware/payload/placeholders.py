"""Recognise placeholder text that RDIs write instead of leaving a field empty.

BonaRes and Thünen (GeoNode CSW) fill optional ISO 19139 elements with ``None`` or
``No information provided``; e!DAL renders an unexpanded ``$licenseURL`` template. These
are not metadata and are treated as absent — but only where the repository's
``mapper.placeholders`` says so. Nothing counts as a placeholder by default, so every
value the harvester drops is visible in the configuration.

Matching is exact on the whole value (case-insensitive, surrounding whitespace ignored),
so a sentence that merely contains "none" is kept.
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

_TEMPLATE_RE = re.compile(r"^(?:\$\{?[A-Za-z_]\w*\}?|\{\{\s*[A-Za-z_][\w.]*\s*\}\})$")


class PlaceholderConfig(BaseModel):
    """Per-RDI placeholder text treated as absent (``mapper.placeholders``)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    values: Annotated[
        frozenset[str],
        Field(
            description=(
                "Whole-value placeholders this RDI writes instead of leaving a field empty "
                "(case-insensitive, surrounding whitespace ignored), e.g. 'None', 'No information provided'. "
                "Matching values in optional fields are treated as absent; required fields "
                "(identifier, title, abstract) are not affected."
            ),
        ),
    ] = frozenset()
    unrendered_templates: Annotated[
        bool,
        Field(
            description=(
                "Also treat unrendered template variables ($var, ${var}, {{var}}) as placeholders, "
                "e.g. e!DAL's '$licenseURL'."
            ),
        ),
    ] = False

    @field_validator("values")
    @classmethod
    def _fold_values(cls, values: frozenset[str]) -> frozenset[str]:
        return frozenset(v.strip().casefold() for v in values if v.strip())

    def matches(self, value: str) -> bool:
        """Whether ``value`` is one of :attr:`values` or, if enabled, an unrendered template."""
        text = value.strip()
        return text.casefold() in self.values or (self.unrendered_templates and bool(_TEMPLATE_RE.match(text)))
