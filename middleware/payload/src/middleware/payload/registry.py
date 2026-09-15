"""Reusable registry for mapping keys to concrete implementation types.

Shared by ``middleware.payload`` (DataMappers) and protocol plugins
(e.g. linked_data Sitemap/Dataset registries).
"""

from __future__ import annotations

from collections.abc import Callable, ItemsView
from typing import cast


class Registry[K, V]:
    """Registry for mapping keys to concrete implementation types."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._registry: dict[K, type[V]] = {}

    def register[T](self, key: K) -> Callable[[type[T]], type[T]]:
        """Return a decorator to register a concrete implementation for the given key.

        ``T`` is independent of ``V`` so decorated subclasses keep their own
        constructor signatures (``Callable[[type[V]], type[V]]`` would erase them
        to the registry value type). The nested function avoids annotating with
        method-scoped ``T`` (basedpyright forbids that on instance attributes).
        """

        def decorator(subclass: type[V]) -> type[V]:
            self._registry[key] = subclass
            return subclass

        return cast(Callable[[type[T]], type[T]], decorator)

    def __getitem__(self, key: K) -> type[V]:
        """Return the registered implementation for the given key."""
        return cast(type[V], self._registry[key])

    def __setitem__(self, key: K, value: type[V]) -> None:
        """Register a concrete implementation for the given key."""
        self._registry[key] = value

    def __contains__(self, key: K) -> bool:
        """Return whether the registry contains the given key."""
        return key in self._registry

    def items(self) -> ItemsView[K, type[V]]:
        """Return the registry items."""
        return self._registry.items()
