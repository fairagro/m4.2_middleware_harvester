"""Linked Data graph-to-ARC mapper abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar, cast

from rdflib import Graph

from ..config import Config, PayloadType
from ..registry import Registry

M = TypeVar("M", bound="LinkedDataMapper")


class LinkedDataMapper(ABC):
    """Maps a parsed Linked Data RDF graph to ARC RO-Crate JSON-LD."""

    registry: Registry[PayloadType, LinkedDataMapper] = Registry()

    @classmethod
    def register(cls, payload_type: PayloadType) -> Callable[[type[M]], type[M]]:
        """Register a concrete LinkedDataMapper implementation for the given payload type."""

        def decorator(subclass: type[M]) -> type[M]:
            cls.registry[payload_type] = cast(type[LinkedDataMapper], subclass)
            return subclass

        return decorator

    @classmethod
    def from_config(cls, config: Config) -> LinkedDataMapper:
        """Construct a mapper from plugin configuration.

        Subclasses that need config fields (e.g. resource base URL) override this.
        """
        _ = config
        return cls()

    @abstractmethod
    def map_graph(self, graph: Graph) -> str:
        """Return a serialized RO-Crate JSON-LD string for the given graph."""
        raise NotImplementedError
