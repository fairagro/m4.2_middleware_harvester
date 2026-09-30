"""Shared DataMapper abstraction and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Any, ClassVar, TypeVar, cast, get_args, get_origin

from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.parsed_payload import ParsedPayload
from middleware.payload.registry import Registry

TDataMapper = TypeVar("TDataMapper", bound="DataMapper[Any]")


class DataMapper[TContext](ABC):
    """Maps an intermediate payload to ``HarvestedArc``.

    ``TContext`` is the mapper-family context type (e.g. ``MappingContext`` for RDF).

    Mappers must not perform protocol discovery or HTTP fetching of source
    catalogs. Selection is by explicit registry key (``MapperType``).
    """

    # Shared store for all context specializations (erased to Any at the registry).
    registry: Registry[MapperType, DataMapper[Any]] = Registry()
    accepts: ClassVar[PayloadKind]

    @classmethod
    def register(cls, mapper_type: MapperType) -> Callable[[type[TDataMapper]], type[TDataMapper]]:
        """Register a concrete DataMapper implementation for the given type."""
        return cls.registry.register(mapper_type)

    @classmethod
    def resolve_context_type(cls) -> type[Any]:
        """Return the ``TContext`` argument from the nearest ``DataMapper[...]`` base."""
        for klass in cls.__mro__:
            for base in getattr(klass, "__orig_bases__", ()):
                if get_origin(base) is DataMapper:
                    args = get_args(base)
                    if args:
                        return cast(type[Any], args[0])
        raise TypeError(f"{cls.__name__} does not specialize DataMapper[TContext]")

    @classmethod
    def registered_class_for_context(
        cls,
        mapper_type: MapperType,
        context_type: type[Any],
    ) -> type[DataMapper[Any]]:
        """Return a registry entry whose ``map`` context accepts ``context_type``.

        The shared registry erases ``TContext``. Callers that always pass a concrete
        context (e.g. OAI-PMH → ``MappingContext``) MUST use this helper so a
        misconfigured ``mapper.type`` fails at construction instead of inside ``map``.
        """
        mapper_cls = cls.registry[mapper_type]
        resolved = mapper_cls.resolve_context_type()
        # Caller passes ``context_type`` into ``map(..., context: TContext)``.
        if not issubclass(context_type, resolved):
            raise TypeError(
                f"mapper.type {mapper_type} expects context {resolved.__name__}, "
                f"but caller requires {context_type.__name__}"
            )
        return mapper_cls

    @classmethod
    def from_config(cls, config: MapperConfig, *, resource_base_url: str | None = None) -> DataMapper[TContext]:
        """Construct a mapper from repository mapper configuration.

        Subclasses that need config fields override this. ``resource_base_url``
        is an optional caller-supplied fallback when ``config.resource_base_url``
        is unset (e.g. derived from a plugin sitemap URL).
        """
        _ = config, resource_base_url
        return cls()

    @abstractmethod
    def map(self, payload: ParsedPayload, context: TContext) -> Iterable[HarvestedArc]:
        """Map ``payload`` to harvested ARCs using a family-specific ``context``."""
        raise NotImplementedError
