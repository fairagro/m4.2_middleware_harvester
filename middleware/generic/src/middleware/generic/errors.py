"""Errors for the generic harvest plugin."""

from middleware.harvester.errors import HarvesterError
from middleware.parsing.errors import ParserError


class GenericError(HarvesterError):
    """Base error for the generic harvest plugin."""


class GenericProtocolError(GenericError):
    """Protocol discovery failed."""


# Backward-compatible alias for shared parser failures (owned by middleware.parsing).
GenericParserError = ParserError
