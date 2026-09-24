"""Errors for the OAI-PMH harvest plugin."""

from middleware.harvester.errors import HarvesterError


class OaiPmhError(HarvesterError):
    """Base error for the OAI-PMH plugin."""


class OaiPmhProtocolError(OaiPmhError):
    """OAI-PMH protocol / client failure."""


class OaiPmhRobotsDisallowedError(OaiPmhError):
    """OAI endpoint disallowed by robots.txt."""
