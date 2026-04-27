"""Custom exceptions for the Schema.org to ARC harvester."""

from middleware.harvester.errors import HarvesterError


class SchemaOrgHarvesterError(HarvesterError):
    """Base exception for Schema.org harvester errors."""


class SchemaOrgFetchError(SchemaOrgHarvesterError):
    """Error fetching Schema.org JSON data."""


class SchemaOrgParseError(SchemaOrgHarvesterError):
    """Error parsing Schema.org JSON data."""


class SchemaOrgMappingError(SchemaOrgHarvesterError):
    """Error mapping Schema.org data to ARC."""
