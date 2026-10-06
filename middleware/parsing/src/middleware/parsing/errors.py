"""Errors for shared PayloadParser implementations."""

from middleware.contracts.errors import HarvesterError


class ParserError(HarvesterError):
    """Payload parse failed."""
