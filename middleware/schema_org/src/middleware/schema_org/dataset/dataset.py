"""Schema.org dataset abstractions and concrete dataset wrappers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar, cast

from rdflib import Graph

from middleware.harvester.nice_http_client import NiceHttpClient

from ..config import Config, DatasetType
from ..errors import SchemaOrgDatasetError
from ..registry import Registry


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

    registry: Registry[DatasetType, Dataset] = Registry()

    @classmethod
    def register(cls, dataset_type: DatasetType) -> Callable[[type[T]], type[T]]:
        """Register a concrete Dataset implementation for the given dataset type."""

        def decorator(subclass: type[T]) -> type[T]:
            cls.registry[dataset_type] = cast(type[Dataset], subclass)
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

    @staticmethod
    async def _fetch_html(url: str, client: NiceHttpClient) -> str:
        """Fetch an HTML payload with harvesting policy (robots, rate limit, retry)."""
        try:
            response = await client.get_with_policy(url, follow_redirects=True)
            return response.text
        except Exception as exc:  # noqa: BLE001
            raise SchemaOrgDatasetError(f"Failed to fetch dataset URL {url}: {exc}") from exc

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
