"""Reusable registry implementation for Schema.org plugin components."""

from __future__ import annotations

from collections.abc import Callable, ItemsView
from typing import Generic, TypeVar, cast

K = TypeVar("K")
V = TypeVar("V")


class Registry(Generic[K, V]):  # noqa: UP046
    """Registry for mapping keys to concrete implementation types."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._registry: dict[K, type[V]] = {}

    def register(self, key: K) -> Callable[[type[V]], type[V]]:
        """Return a decorator to register a concrete implementation for the given key."""

        def decorator(subclass: type[V]) -> type[V]:
            self._registry[key] = subclass
            return subclass

        return decorator

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
