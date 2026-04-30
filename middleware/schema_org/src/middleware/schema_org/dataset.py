"""Schema.org dataset abstractions and concrete dataset wrappers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from rdflib import Graph

from .config import DatasetType


@dataclass
class DiscoveryResult:
    """Base class for results yielded by Sitemap discovery."""


@dataclass
class UrlDiscoveryResult(DiscoveryResult):
    """Discovery result representing a dataset URL."""

    url: str


T = TypeVar("T", bound="Dataset")


class Dataset(ABC):
    """Abstract wrapper around a Schema.org dataset payload."""

    registry: dict[DatasetType, type[Dataset]] = {}

    @classmethod
    def register(cls, dataset_type: DatasetType) -> Callable[[type[T]], type[T]]:
        """Register a concrete Dataset implementation for the given dataset type."""

        def decorator(subclass: type[T]) -> type[T]:
            cls.registry[dataset_type] = subclass
            return subclass

        return decorator

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Return the stable identifier for this dataset."""
        raise NotImplementedError

    @abstractmethod
    async def to_graph(self) -> Graph:
        """Return the dataset payload as an RDF graph."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_discovery_result(cls, discovery_result: DiscoveryResult) -> Dataset:
        """Create a Dataset instance from a discovery result."""
        raise NotImplementedError


@Dataset.register(DatasetType.dummy)
class DummyDataset(Dataset):
    """Minimal Dataset implementation used as a placeholder."""

    def __init__(self, identifier: str, graph: Graph | None = None) -> None:
        """Initialize the dummy dataset with an identifier and an optional graph."""
        self._identifier = identifier
        self._graph = graph or Graph()

    @property
    def identifier(self) -> str:
        """Return the stable identifier for this dataset."""
        return self._identifier

    @classmethod
    def from_discovery_result(cls, discovery_result: DiscoveryResult) -> Dataset:
        """Construct a DummyDataset from a discovery result."""
        if isinstance(discovery_result, UrlDiscoveryResult):
            return cls(discovery_result.url)
        return cls(str(discovery_result))

    async def to_graph(self) -> Graph:
        """Return the dataset payload as an rdflib.Graph."""
        return self._graph
