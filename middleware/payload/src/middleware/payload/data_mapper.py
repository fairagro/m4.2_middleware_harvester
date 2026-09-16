"""Shared DataMapper abstraction and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import ClassVar, TypeVar

from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.parsed_payload import ParsedPayload
from middleware.payload.registry import Registry

TDataMapper = TypeVar("TDataMapper", bound="DataMapper")


class DataMapper(ABC):
    """Maps an intermediate payload to ``HarvestedArc``.

    Mappers must not perform protocol discovery or HTTP fetching of source
    catalogs. Selection is by explicit registry key (``MapperType``).
    """

    registry: Registry[MapperType, DataMapper] = Registry()
    accepts: ClassVar[PayloadKind]

    @classmethod
    def register(cls, mapper_type: MapperType) -> Callable[[type[TDataMapper]], type[TDataMapper]]:
        """Register a concrete DataMapper implementation for the given type."""
        return cls.registry.register(mapper_type)

    @classmethod
    def from_config(cls, config: MapperConfig, *, resource_base_url: str | None = None) -> DataMapper:
        """Construct a mapper from repository mapper configuration.

        Subclasses that need config fields override this. ``resource_base_url``
        is an optional caller-supplied fallback when ``config.resource_base_url``
        is unset (e.g. derived from a plugin sitemap URL).
        """
        _ = config, resource_base_url
        return cls()

    @abstractmethod
    def map(self, payload: ParsedPayload, context: object) -> Iterable[HarvestedArc]:
        """Map ``payload`` to harvested ARCs.

        ``context`` is mapper-family specific (e.g. ``MappingContext`` for RDF).
        """
        raise NotImplementedError
