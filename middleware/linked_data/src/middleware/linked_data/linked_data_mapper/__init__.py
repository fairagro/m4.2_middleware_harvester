"""Linked Data mapper abstractions and vocabulary-specific implementations."""

from .general_schema_org_mapper import GeneralSchemaOrgMapper, ResolvedField
from .linked_data_mapper import LinkedDataMapper, MappingContext
from .openagrar_schema_org_mapper import OpenAgrarSchemaOrgMapper
from .regal_mapper import RegalMapper

__all__ = [
    "LinkedDataMapper",
    "MappingContext",
    "GeneralSchemaOrgMapper",
    "OpenAgrarSchemaOrgMapper",
    "RegalMapper",
    "ResolvedField",
]
