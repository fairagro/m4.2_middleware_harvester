"""Linked Data graph-to-ARC mapper abstractions."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TypeVar, cast

from rdflib import Graph

from middleware.harvester.plugin_base import HarvestedArc

from ..config import Config, PayloadType
from ..registry import Registry
from .stable_graph import StableGraph

M = TypeVar("M", bound="LinkedDataMapper")


@dataclass(frozen=True)
class MappingContext:
    """Discovery context for one ``map_graph`` call (not part of StableGraph)."""

    source_url: str | None = None
    harvest_source_id: str | None = None


class LinkedDataMapper(ABC):
    """Maps a parsed Linked Data RDF graph to ARC RO-Crate JSON-LD.

    ``map_graph`` wraps the graph via :meth:`_stable_wrap`, then passes the
    ``StableGraph`` explicitly into :meth:`_map_graph`. Subclasses must not store
    the wrap on ``self`` — the plugin maps concurrently via ``asyncio.to_thread``.
    Per-call helpers (e.g. Schema.org ``_SchemaOrgRun``) or threading ``stable``
    through private methods are fine; a ``_*Run`` class is not mandatory.

    See ``openspec/specs/linked-data-mapper/design.md`` for the StableGraph vs
    LinkedDataMapper boundary (Faustregel).
    """

    registry: Registry[PayloadType, LinkedDataMapper] = Registry()

    _FORBIDDEN_ID_CHARS = re.compile(r"[^a-zA-Z0-9 _-]")

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

    def map_graph(self, graph: Graph, context: MappingContext) -> Iterable[HarvestedArc]:
        """Return harvested ARCs (JSON + composition counts) for the given graph.

        Wraps ``graph`` once and passes the ``StableGraph`` into :meth:`_map_graph`.

        ``context`` is required. Callers without discovery data pass
        ``MappingContext()`` (fields default to ``None``).

        ``context.harvest_source_id`` is an optional RDI-native catalog id from the
        sitemap/discovery layer (e.g. MyCoRe Solr ``id``). When supplied, Schema.org
        mappers use it as the primary harvest-stable ``Investigation.identifier``,
        even when the graph contains DOIs.

        ``context.source_url`` is the discovered landing/page URL. When no
        ``harvest_source_id`` is supplied, Schema.org mappers may use a sanitized
        ``source_url`` as the primary harvest-stable identifier before graph URL or
        DOI fallbacks.

        Returns an iterable of HarvestedArc objects. Mappers that handle a single
        entity per graph yield an iterable with exactly one element. Mappers that
        handle multiple entities (e.g. multiple Schema.org Datasets) yield multiple
        elements. Callers that need a concrete sequence should materialize with
        ``list(...)``.
        """
        return self._map_graph(graph, context, self._stable_wrap(graph))

    @abstractmethod
    def _map_graph(self, graph: Graph, context: MappingContext, stable: StableGraph) -> Iterable[HarvestedArc]:
        """Map ``graph`` using the caller-provided ``stable`` wrap (see :meth:`map_graph`)."""
        raise NotImplementedError

    def _stable_wrap(self, graph: Graph) -> StableGraph:
        """Wrap ``graph`` for this mapper. Override for vocabulary-specific policy."""
        return StableGraph.wrap(graph)

    @classmethod
    def sanitize_identifier(cls, raw: str) -> str:
        """Make *raw* safe for arctrl ``Investigation.identifier``.

        Strips a leading ``http(s)://``, replaces characters outside
        ``[A-Za-z0-9 _-]`` with ``_``, collapses repeats, and trims underscores.
        """
        stripped = re.sub(r"^https?://", "", raw)
        sanitized = cls._FORBIDDEN_ID_CHARS.sub("_", stripped)
        return re.sub(r"_{2,}", "_", sanitized).strip("_")

    @staticmethod
    def to_identifier_slug(title: str) -> str | None:
        """Slugify a non-empty title for ARC identifiers (max 80 chars).

        Returns ``None`` when ``title`` is blank or sanitizes to an empty slug.
        Callers that invent display titles (e.g. Regal ``Untitled``) must supply
        that policy themselves; Schema.org refuses missing ``schema:name``.
        """
        if not title or not title.strip():
            return None
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        return slug[:80] or None

    @staticmethod
    def pick_canonical_doi(dois: list[str]) -> str | None:
        """Return the lexicographic minimum DOI (casefold, then original string)."""
        return min(dois, key=lambda doi: (doi.casefold(), doi)) if dois else None

    def resolve_harvest_source_identifier(self, context: MappingContext) -> str | None:
        """Stable harvest-unit identifier from discovery (catalog id or page URL)."""
        if context.harvest_source_id and context.harvest_source_id.strip():
            return context.harvest_source_id.strip()
        if context.source_url and context.source_url.strip().startswith(("http://", "https://")):
            return self.sanitize_identifier(context.source_url.strip())
        return None
