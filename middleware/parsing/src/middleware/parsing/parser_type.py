"""Parser type registry keys."""

from enum import StrEnum


class ParserType(StrEnum):
    """Registered PayloadParser kinds for shared harvesting parsers."""

    html_jsonld = "html_jsonld"
