"""Abstract Schema.org harvester interfaces and dummy implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from rdflib import Graph

from .config import Config


class Dataset(ABC):
    """Abstract wrapper around a Schema.org dataset payload."""

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

    def __init__(self, config: Config) -> None:
        """Create a new Sitemap configured for a specific source."""
        self.config = config

    @abstractmethod
    async def discover(self) -> AsyncGenerator[Dataset, None]:
        """Asynchronously yield Dataset objects found in the configured sitemap."""
        if False:  # pragma: no cover
            yield DummyDataset("unused")  # type: ignore[reportUndefinedVariable]
        raise NotImplementedError


class SchemaOrgMapper(ABC):
    """Maps a parsed Schema.org RDF graph to ARC RO-Crate JSON-LD."""

    @abstractmethod
    def map_graph(self, graph: Graph) -> str:
        """Return a serialized RO-Crate JSON-LD string for the given graph."""
        raise NotImplementedError


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


class DummySchemaOrgMapper(SchemaOrgMapper):
    """Minimal mapper implementation that returns an empty RO-Crate JSON-LD stub."""

    def map_graph(self, _graph: Graph) -> str:
        """Serialize the supplied graph to a placeholder RO-Crate JSON-LD string."""
        return '{"@context":"https://w3id.org/ro/crate/1.1","@graph":[]}'
