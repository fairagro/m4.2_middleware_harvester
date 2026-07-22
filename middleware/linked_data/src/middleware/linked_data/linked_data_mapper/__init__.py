"""Linked Data mapper abstractions and vocabulary-specific implementations."""

from .general_schema_org_mapper import GeneralSchemaOrgMapper
from .linked_data_mapper import LinkedDataMapper

__all__ = ["LinkedDataMapper", "GeneralSchemaOrgMapper"]
