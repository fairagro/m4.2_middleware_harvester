"""Linked Data graph-to-ARC mapper abstractions."""

from __future__ import annotations

import re
from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar, override

from rdflib import Graph

from middleware.payload.data_mapper import DataMapper
from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.kinds import PayloadKind
from middleware.payload.linked_data_mapper.stable_graph import StableGraph
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.parsed_payload import ParsedPayload


@dataclass(frozen=True)
class MappingContext:
    """Discovery context for one ``map_graph`` call (not part of StableGraph)."""

    source_url: str | None = None
    harvest_source_id: str | None = None
    html_title: Callable[[], str | None] | None = None


class LinkedDataMapper(DataMapper[MappingContext]):
    """Maps a parsed Linked Data RDF graph to ARC RO-Crate JSON-LD.

    ``map_graph`` wraps the graph via :meth:`_stable_wrap`, then passes the
    ``StableGraph`` explicitly into :meth:`_map_graph`. Subclasses must not store
    the wrap on ``self`` — the plugin maps concurrently via ``asyncio.to_thread``.
    Per-call helpers (e.g. Schema.org ``_SchemaOrgRun``) or threading ``stable``
    through private methods are fine; a ``_*Run`` class is not mandatory.

    See ``openspec/specs/linked-data-mapper/design.md`` for the StableGraph vs
    LinkedDataMapper boundary (Faustregel).
    """

    accepts: ClassVar[PayloadKind] = PayloadKind.rdf_graph

    _FORBIDDEN_ID_CHARS = re.compile(r"[^a-zA-Z0-9 _-]")

    @classmethod
    def registered_class(cls, mapper_type: MapperType) -> type[LinkedDataMapper]:
        """Return the ``DataMapper.registry`` entry narrowed to ``LinkedDataMapper``."""
        mapper_cls = DataMapper.registry[mapper_type]
        if not issubclass(mapper_cls, cls):
            raise TypeError(f"mapper.type {mapper_type} is {mapper_cls.__name__}, not a {cls.__name__}")
        return mapper_cls

    @classmethod
    @override
    def from_config(cls, config: MapperConfig, *, resource_base_url: str | None = None) -> LinkedDataMapper:
        """Construct a mapper from repository mapper configuration.

        Subclasses that need config fields (e.g. resource base URL) override this.
        """
        _ = config, resource_base_url
        return cls()

    @override
    def map(self, payload: ParsedPayload, context: MappingContext) -> Iterable[HarvestedArc]:
        """Map an ``rdf_graph`` ``ParsedPayload`` using ``MappingContext``."""
        if payload.kind != PayloadKind.rdf_graph:
            raise ValueError(f"LinkedDataMapper accepts {PayloadKind.rdf_graph}, got {payload.kind}")
        if not isinstance(payload.value, Graph):
            raise TypeError(f"rdf_graph payload value must be rdflib.Graph, got {type(payload.value)!r}")
        return self.map_graph(payload.value, context)

    def map_graph(self, graph: Graph, context: MappingContext) -> Iterable[HarvestedArc]:
        """Return harvested ARCs (JSON + composition counts) for the given graph.

        Wraps ``graph`` once and passes the ``StableGraph`` into :meth:`_map_graph`.

        ``context`` is required. Callers without discovery data pass
        ``MappingContext()`` (fields default to ``None``).
        """
        return self._map_graph(graph, context, self._stable_wrap(graph))

    @abstractmethod
    def _map_graph(self, graph: Graph, context: MappingContext, stable: StableGraph) -> Iterable[HarvestedArc]:
        """Map ``graph`` using the caller-provided ``stable`` wrap (see :meth:`map_graph`)."""
        raise NotImplementedError

    def _stable_wrap(self, graph: Graph) -> StableGraph:  # noqa: PLR6301
        """Wrap ``graph`` for this mapper. Override for vocabulary-specific policy.

        Instance-scoped so a subclass's wrap policy (term namespaces, label
        predicates) can come from instance state — config or a dialect profile —
        rather than only from a hardcoded class body.
        """
        return StableGraph.wrap(graph)

    @classmethod
    def sanitize_identifier(cls, raw: str) -> str:
        """Make *raw* safe for arctrl ``Investigation.identifier``."""
        stripped = re.sub(r"^https?://", "", raw)
        sanitized = cls._FORBIDDEN_ID_CHARS.sub("_", stripped)
        return re.sub(r"_{2,}", "_", sanitized).strip("_")

    @staticmethod
    def to_identifier_slug(title: str) -> str | None:
        """Slugify a non-empty title for ARC identifiers (max 80 chars)."""
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
