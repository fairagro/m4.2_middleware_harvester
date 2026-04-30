"""Schema.org graph-to-ARC mapper abstractions and concrete mappers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar

from rdflib import Graph

from .config import PayloadType

M = TypeVar("M", bound="SchemaOrgMapper")


class SchemaOrgMapper(ABC):
    """Maps a parsed Schema.org RDF graph to ARC RO-Crate JSON-LD."""

    registry: dict[PayloadType, type[SchemaOrgMapper]] = {}

    @classmethod
    def register(cls, payload_type: PayloadType) -> Callable[[type[M]], type[M]]:
        """Register a concrete SchemaOrgMapper implementation for the given payload type."""

        def decorator(subclass: type[M]) -> type[M]:
            cls.registry[payload_type] = subclass
            return subclass

        return decorator

    @abstractmethod
    def map_graph(self, graph: Graph) -> str:
        """Return a serialized RO-Crate JSON-LD string for the given graph."""
        raise NotImplementedError


@SchemaOrgMapper.register(PayloadType.dummy)
class DummySchemaOrgMapper(SchemaOrgMapper):
    """Minimal mapper implementation that returns an empty RO-Crate JSON-LD stub."""

    def map_graph(self, _graph: Graph) -> str:
        """Serialize the supplied graph to a placeholder RO-Crate JSON-LD string."""
        return '{"@context":"https://w3id.org/ro/crate/1.1","@graph":[]}'
