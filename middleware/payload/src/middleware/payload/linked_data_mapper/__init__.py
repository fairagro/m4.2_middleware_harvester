"""Linked Data mapper abstractions and vocabulary-specific implementations."""

from .linked_data_mapper import LinkedDataMapper, MappingContext
from .register_builtins import register_builtin_mappers

__all__ = [
    "LinkedDataMapper",
    "MappingContext",
    "register_builtin_mappers",
]
