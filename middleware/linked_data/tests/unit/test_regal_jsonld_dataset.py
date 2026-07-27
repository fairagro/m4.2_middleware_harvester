"""Unit tests for Regal JSON-LD dataset parsing."""

from __future__ import annotations

import pytest
from rdflib.namespace import DCTERMS, RDF

from middleware.linked_data.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType
from middleware.linked_data.dataset import JsonLdDiscoveryResult, UrlDiscoveryResult
from middleware.linked_data.dataset.regal_jsonld import RegalJsonLdDataset
from middleware.linked_data.errors import LinkedDataDatasetError
from middleware.linked_data.linked_data_mapper.regal_mapper import RESEARCH_DATA_TYPE

_MINIMAL_CONTEXT = {
    "@vocab": "http://hbz-nrw.de/regal#",
    "title": {"@id": "http://purl.org/dc/terms/title"},
    "description": {"@id": "http://purl.org/dc/terms/description"},
    "rdftype": {"@id": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type", "@type": "@id"},
    "doi": {"@id": "http://hbz-nrw.de/regal#doi"},
    "prefLabel": {"@id": "http://www.w3.org/2004/02/skos/core#prefLabel"},
}


def _config() -> Config:
    return Config(
        sitemap_url="https://frl.publisso.de/find",
        sitemap_type=SitemapType.regal_find,
        dataset_type=DatasetType.regal_jsonld,
        payload_type=PayloadType.regal_general,
        http=NiceHttpClientConfig(respect_robots_txt=False),
    )


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "@context": _MINIMAL_CONTEXT,
        "@id": "frl:123",
        "title": ["Example Dataset"],
        "description": ["A description"],
        "rdftype": ["http://hbz-nrw.de/regal#ResearchData"],
        "doi": "10.4126/FRL01-0000123",
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_regal_jsonld_dataset_parses_inline_payload() -> None:
    discovery = JsonLdDiscoveryResult(identifier="frl:123", payload=_payload())
    dataset = RegalJsonLdDataset.from_discovery_result(discovery, client=None, config=_config())
    assert dataset.identifier == "frl:123"

    graph = await dataset.to_graph()
    assert (None, RDF.type, RESEARCH_DATA_TYPE) in graph
    assert any(str(o) == "Example Dataset" for o in graph.objects(None, DCTERMS.title))
    subjects = {str(s) for s in graph.subjects(RDF.type, RESEARCH_DATA_TYPE)}
    assert "https://frl.publisso.de/resource/frl:123" in subjects


@pytest.mark.asyncio
async def test_regal_jsonld_dataset_uses_configured_resource_base_url() -> None:
    config = Config(
        sitemap_url="https://frl.publisso.de/find",
        sitemap_type=SitemapType.regal_find,
        dataset_type=DatasetType.regal_jsonld,
        payload_type=PayloadType.regal_general,
        resource_base_url="https://repository.publisso.de/resource/",
        http=NiceHttpClientConfig(respect_robots_txt=False),
    )
    discovery = JsonLdDiscoveryResult(identifier="frl:123", payload=_payload())
    dataset = RegalJsonLdDataset.from_discovery_result(discovery, client=None, config=config)
    graph = await dataset.to_graph()
    subjects = {str(s) for s in graph.subjects(RDF.type, RESEARCH_DATA_TYPE)}
    assert "https://repository.publisso.de/resource/frl:123" in subjects


@pytest.mark.asyncio
async def test_regal_jsonld_dataset_rejects_url_discovery_result() -> None:
    with pytest.raises(ValueError, match="Unsupported discovery result"):
        RegalJsonLdDataset.from_discovery_result(
            UrlDiscoveryResult("https://example.org/page"),
            client=None,
            config=_config(),
        )


@pytest.mark.asyncio
async def test_regal_jsonld_dataset_raises_on_invalid_jsonld() -> None:
    discovery = JsonLdDiscoveryResult(
        identifier="frl:bad",
        payload={"@context": 123, "@id": "frl:bad"},
    )
    dataset = RegalJsonLdDataset.from_discovery_result(discovery, client=None, config=_config())
    with pytest.raises(LinkedDataDatasetError):
        await dataset.to_graph()
