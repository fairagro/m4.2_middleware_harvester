"""Exceptions for the Schema.org harvester plugin.

This module defines the plugin-specific exception hierarchy used by the
Schema.org implementation. All plugin-specific errors inherit from
`HarvesterError` in the central harvester package.
"""

from middleware.harvester.errors import HarvesterError


class SchemaOrgError(HarvesterError):
    """Base exception for Schema.org plugin failures."""


class SchemaOrgDatasetError(SchemaOrgError):
    """Raised when a Schema.org dataset payload cannot be fetched or parsed."""


class SchemaOrgSitemapError(SchemaOrgError):
    """Raised when sitemap discovery or parsing fails."""
