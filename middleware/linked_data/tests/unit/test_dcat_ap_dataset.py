"""Unit tests for DcatApDataset (pre-extracted subgraph passthrough)."""

from __future__ import annotations

import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS

from middleware.linked_data.config import Config, DatasetType, NiceHttpClientConfig, SitemapType
from middleware.linked_data.dataset import UrlDiscoveryResult
from middleware.linked_data.dataset.dcat_ap import DcatApDataset, DcatDatasetDiscoveryResult


def _config() -> Config:
    return Config(
        sitemap_url="https://example.org/catalog.jsonld",
        sitemap_type=SitemapType.dcat_ap,
        dataset_type=DatasetType.dcat_ap,
        http=NiceHttpClientConfig(respect_robots_txt=False),
    )


@pytest.mark.asyncio
async def test_dcat_ap_dataset_returns_preextracted_graph_unchanged() -> None:
    subject = URIRef("https://example.org/dataset/1")
    graph = Graph()
    graph.add((subject, DCTERMS.title, Literal("Dataset One")))

    discovery = DcatDatasetDiscoveryResult(identifier=str(subject), graph=graph)
    dataset = DcatApDataset.from_discovery_result(discovery, client=None, config=_config())

    assert dataset.identifier == str(subject)
    assert await dataset.to_graph() is graph


def test_dcat_ap_dataset_rejects_other_discovery_result_types() -> None:
    with pytest.raises(ValueError, match="Unsupported discovery result"):
        DcatApDataset.from_discovery_result(
            UrlDiscoveryResult("https://example.org/page"),
            client=None,
            config=_config(),
        )
