"""DCAT-AP dataset wrapper for pre-extracted per-record RDF subgraphs."""

from __future__ import annotations

from dataclasses import dataclass

from rdflib import Graph

from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.linked_data.config import Config, DatasetType
from middleware.linked_data.dataset.dataset import Dataset, DiscoveryResult


@dataclass
class DcatDatasetDiscoveryResult(DiscoveryResult):
    """Discovery result carrying a pre-extracted per-dataset RDF subgraph.

    Unlike ``JsonLdDiscoveryResult`` (one inline JSON-LD node), a DCAT-AP
    catalog page describes many datasets in one JSON-LD document.
    ``DcatApSitemap`` parses each page once and extracts a small per-dataset
    subgraph (the dataset's Concise Bounded Description plus one hop into its
    ``dcat:distribution`` / ``dcterms:publisher`` / ``dcat:contactPoint`` /
    ``dcterms:spatial`` objects), so ``DcatApDataset`` needs no further HTTP
    fetch or parsing. This type is intentionally local to the
    ``DcatApSitemap`` / ``DcatApDataset`` pair, not a shared
    ``middleware.parsing.discovery`` type.
    """

    graph: Graph


@Dataset.register(DatasetType.dcat_ap)
class DcatApDataset(Dataset):
    """Dataset wrapper for a pre-extracted DCAT-AP per-record subgraph (no HTTP fetch)."""

    def __init__(self, identifier: str, graph: Graph) -> None:
        """Initialize with the stable dataset IRI and its pre-extracted subgraph."""
        self._identifier = identifier
        self._graph = graph

    @property
    def identifier(self) -> str:
        """The dataset's IRI (``dcat:Dataset`` subject) as discovered."""
        return self._identifier

    @classmethod
    def from_discovery_result(
        cls,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: Config,
    ) -> Dataset:
        """Construct a DcatApDataset from a pre-extracted-subgraph discovery result."""
        del client, config  # Subgraph is already extracted; no HTTP fetch or config needed.
        if not isinstance(discovery_result, DcatDatasetDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")
        return cls(discovery_result.identifier, discovery_result.graph)

    async def to_graph(self) -> Graph:
        """Return the pre-extracted per-dataset RDF subgraph."""
        return self._graph
