"""Errors for shared PayloadParser implementations."""

from middleware.harvester.errors import HarvesterError


class ParserError(HarvesterError):
    """Payload parse failed."""
