"""Errors for the generic harvest plugin."""

from middleware.contracts.errors import HarvesterError


class GenericError(HarvesterError):
    """Base error for the generic harvest plugin."""


class GenericProtocolError(GenericError):
    """Protocol discovery failed."""
