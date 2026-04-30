"""Abstract Schema.org harvester interfaces and dummy implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Callable
from typing import TypeVar

from rdflib import Graph

from .config import Config, DatasetType, PayloadType, SitemapType

T = TypeVar("T", bound="Dataset")
S = TypeVar("S", bound="Sitemap")
M = TypeVar("M", bound="SchemaOrgMapper")


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


class Sitemap(ABC):
    """Abstract sitemap provider that yields Dataset objects asynchronously."""

    registry: dict[SitemapType, type[Sitemap]] = {}

    def __init__(
        self,
        config: Config,
        dataset_factory: Callable[[str], Dataset] | None = None,
    ) -> None:
        """Create a new Sitemap configured for a specific source."""
        self.config = config
        self.dataset_factory = dataset_factory

    @classmethod
    def register(cls, sitemap_type: SitemapType) -> Callable[[type[S]], type[S]]:
        """Register a concrete Sitemap implementation for the given sitemap type."""

        def decorator(subclass: type[S]) -> type[S]:
            cls.registry[sitemap_type] = subclass
            return subclass

        return decorator

    @abstractmethod
    async def discover(self) -> AsyncGenerator[Dataset, None]:
        """Asynchronously yield Dataset objects found in the configured sitemap."""
        if False:  # pragma: no cover
            yield DummyDataset("unused")  # type: ignore[reportUndefinedVariable]
        raise NotImplementedError


class SchemaOrgMapper(ABC):
    """Maps a parsed Schema.org RDF graph to ARC RO-Crate JSON-LD."""

    registry: dict[PayloadType, type[SchemaOrgMapper]] = {}

    @classmethod
    def register(cls, payload_type: PayloadType) -> Callable[[type[M]], type[M]]:
        """Register a concrete SchemaOrgMapper implementation for the given payload type."""

        def decorator(subclass: type[M]) -> type[M]:
            cls.registry[payload_type] = subclass
            return subclass

        return decorator

    @abstractmethod
    def map_graph(self, graph: Graph) -> str:
        """Return a serialized RO-Crate JSON-LD string for the given graph."""
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

    async def to_graph(self) -> Graph:
        """Return the dataset payload as an rdflib.Graph."""
        return self._graph


class DummySitemap(Sitemap):
    """Minimal Sitemap implementation producing no datasets."""

    async def discover(self) -> AsyncGenerator[Dataset, None]:
        """Yield no datasets for the placeholder implementation."""
        if False:
            yield DummyDataset("unused")


@SchemaOrgMapper.register(PayloadType.dummy)
class DummySchemaOrgMapper(SchemaOrgMapper):
    """Minimal mapper implementation that returns an empty RO-Crate JSON-LD stub."""

    def map_graph(self, _graph: Graph) -> str:
        """Serialize the supplied graph to a placeholder RO-Crate JSON-LD string."""
        return '{"@context":"https://w3id.org/ro/crate/1.1","@graph":[]}'
