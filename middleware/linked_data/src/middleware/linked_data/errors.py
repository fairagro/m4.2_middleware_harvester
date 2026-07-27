"""Exceptions for the Linked Data harvester plugin.

This module defines the plugin-specific exception hierarchy. All plugin-specific
errors inherit from `HarvesterError` in the central harvester package.
"""

from middleware.harvester.errors import HarvesterError


class LinkedDataError(HarvesterError):
    """Base exception for Linked Data plugin failures."""


class LinkedDataDatasetError(LinkedDataError):
    """Raised when a dataset payload cannot be fetched or parsed."""


class LinkedDataSitemapError(LinkedDataError):
    """Raised when sitemap discovery or parsing fails."""
