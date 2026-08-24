"""Linked Data graph-to-ARC mapper abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar, cast

from rdflib import Graph

from middleware.harvester.plugin_base import HarvestedArc

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
    def map_graph(
        self,
        graph: Graph,
        source_url: str | None = None,
        *,
        harvest_source_id: str | None = None,
    ) -> HarvestedArc:
        """Return a harvested ARC (JSON + composition counts) for the given graph.

        ``harvest_source_id`` is an optional RDI-native catalog id from the
        sitemap/discovery layer (e.g. MyCoRe Solr ``id``). When supplied, Schema.org
        mappers use it as the primary harvest-stable ``Investigation.identifier``,
        even when the graph contains DOIs.

        ``source_url`` is the discovered landing/page URL. When no
        ``harvest_source_id`` is supplied, Schema.org mappers may use a sanitized
        ``source_url`` as the primary harvest-stable identifier before graph URL or
        DOI fallbacks.
        """
        raise NotImplementedError
