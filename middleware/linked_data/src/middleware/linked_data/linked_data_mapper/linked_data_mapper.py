"""Linked Data graph-to-ARC mapper abstractions."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TypeVar, cast

from rdflib import Graph
from rdflib.term import Node

from middleware.harvester.plugin_base import HarvestedArc

from ..config import Config, PayloadType
from ..registry import Registry
from .stable_graph import ResourceView, StableGraph

M = TypeVar("M", bound="LinkedDataMapper")


@dataclass(frozen=True)
class MappingContext:
    """Discovery context for one ``map_graph`` call (not part of StableGraph)."""

    source_url: str | None = None
    harvest_source_id: str | None = None


class LinkedDataMapper(ABC):
    """Maps a parsed Linked Data RDF graph to ARC RO-Crate JSON-LD.

    ``map_graph`` opens a StableGraph session (via :meth:`_stable_wrap`), then
    delegates to :meth:`_map_graph`. Subclasses read RDF via :meth:`view` /
    :attr:`stable` during that call. Vocabulary-specific wrap options belong
    in :meth:`_stable_wrap`, not on this ABC.

    See ``openspec/specs/linked-data-mapper/design.md`` for the StableGraph vs
    LinkedDataMapper boundary (Faustregel).
    """

    registry: Registry[PayloadType, LinkedDataMapper] = Registry()

    _FORBIDDEN_ID_CHARS = re.compile(r"[^a-zA-Z0-9 _-]")

    def __init__(self) -> None:
        """Initialize per-call StableGraph session state."""
        self._stable: StableGraph | None = None

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

    def map_graph(self, graph: Graph, context: MappingContext) -> HarvestedArc:
        """Return a harvested ARC (JSON + composition counts) for the given graph.

        Opens a StableGraph session for the duration of :meth:`_map_graph`.

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
        """
        with self._stable_session(graph):
            return self._map_graph(graph, context)

    @abstractmethod
    def _map_graph(self, graph: Graph, context: MappingContext) -> HarvestedArc:
        """Map ``graph`` while a StableGraph session is active (see :meth:`map_graph`)."""
        raise NotImplementedError

    def _stable_wrap(self, graph: Graph) -> StableGraph:
        """Wrap ``graph`` for this mapper. Override for vocabulary-specific policy."""
        return StableGraph.wrap(graph)

    @contextmanager
    def _stable_session(self, graph: Graph) -> Iterator[StableGraph]:
        """Bind :meth:`_stable_wrap` result as the active StableGraph for the block."""
        self._stable = self._stable_wrap(graph)
        try:
            yield self._stable
        finally:
            self._stable = None

    @property
    def stable(self) -> StableGraph:
        """Active StableGraph for this ``map_graph`` call (set by the session)."""
        return self._stable  # type: ignore[return-value]

    def view(self, subject: Node) -> ResourceView:
        """Return a ResourceView for ``subject`` on the active StableGraph."""
        return self.stable.view(subject)

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
    def to_identifier_slug(title: str) -> str:
        """Slugify a title for use in ARC identifiers (max 80 chars)."""
        if not title:
            return "untitled"
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        return slug[:80] or "untitled"

    @staticmethod
    def pick_canonical_doi(dois: list[str]) -> str | None:
        """Return the lexicographic minimum DOI by Unicode ``casefold``, or None."""
        return min(dois, key=str.casefold) if dois else None

    def resolve_harvest_source_identifier(self, context: MappingContext) -> str | None:
        """Stable harvest-unit identifier from discovery (catalog id or page URL)."""
        if context.harvest_source_id and context.harvest_source_id.strip():
            return context.harvest_source_id.strip()
        if context.source_url and context.source_url.strip().startswith(("http://", "https://")):
            return self.sanitize_identifier(context.source_url.strip())
        return None
