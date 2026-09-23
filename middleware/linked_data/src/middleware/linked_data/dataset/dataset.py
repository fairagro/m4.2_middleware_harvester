"""Linked Data dataset abstractions and concrete dataset wrappers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar

from rdflib import Graph

from middleware.generic.discovery import DiscoveryResult, JsonLdDiscoveryResult, UrlDiscoveryResult
from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import Config, DatasetType
from middleware.payload.registry import Registry

TDataset = TypeVar("TDataset", bound="Dataset")

__all__ = [
    "Dataset",
    "DiscoveryResult",
    "JsonLdDiscoveryResult",
    "UrlDiscoveryResult",
]


class Dataset(ABC):
    """Abstract wrapper around a Linked Data dataset payload."""

    registry: Registry[DatasetType, Dataset] = Registry()

    @classmethod
    def register(cls, dataset_type: DatasetType) -> Callable[[type[TDataset]], type[TDataset]]:
        """Register a concrete Dataset implementation for the given dataset type."""
        return cls.registry.register(dataset_type)

    @property
    @abstractmethod
    def identifier(self) -> str:
        """The stable identifier for this dataset."""
        raise NotImplementedError

    @abstractmethod
    async def to_graph(self) -> Graph:
        """Return the dataset payload as an RDF graph."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_discovery_result(
        cls,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: Config,
    ) -> Dataset:
        """Create a Dataset instance from a discovery result."""
        raise NotImplementedError
