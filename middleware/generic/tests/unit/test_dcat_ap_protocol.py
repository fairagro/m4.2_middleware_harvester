"""Unit tests for DCAT-AP catalog Protocol discovery (Hydra pagination)."""

from __future__ import annotations

import json

import httpx
import pytest
from rdflib import Graph, Namespace
from rdflib.namespace import DCTERMS

import middleware.generic.plugin as plugin_mod
from middleware.contracts.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.contracts.plugin_base import HarvestedArc
from middleware.generic.config import Config
from middleware.generic.errors import GenericProtocolError
from middleware.generic.plugin import GenericPlugin
from middleware.generic.protocol.dcat_ap import DcatApProtocol, DcatApProtocolConfig
from middleware.generic.protocol.protocol import ProtocolType
from middleware.parsing.discovery import JsonLdDiscoveryResult
from middleware.parsing.parser_config import ParserConfig
from middleware.payload.mapper_config import MapperConfig

_CATALOG_URL = "https://example.org/catalog.jsonld"
_FOAF = Namespace("http://xmlns.com/foaf/0.1/")

_PAGE_1: list[dict[str, object]] = [
    {
        "@id": f"{_CATALOG_URL}?page=1",
        "@type": ["http://www.w3.org/ns/hydra/core#PagedCollection"],
        "http://www.w3.org/ns/hydra/core#totalItems": [{"@value": 2}],
        "http://www.w3.org/ns/hydra/core#nextPage": [{"@value": f"{_CATALOG_URL}?page=2"}],
    },
    {
        "@id": "https://example.org/dataset/1",
        "@type": ["http://www.w3.org/ns/dcat#Dataset"],
        "http://purl.org/dc/terms/title": [{"@value": "Dataset One"}],
        "http://www.w3.org/ns/dcat#distribution": [{"@id": "https://example.org/dataset/1/resource/a"}],
        "http://purl.org/dc/terms/publisher": [{"@id": "https://example.org/organization/1"}],
    },
    {
        "@id": "https://example.org/dataset/1/resource/a",
        "@type": ["http://www.w3.org/ns/dcat#Distribution"],
        "http://purl.org/dc/terms/title": [{"@value": "File A"}],
        "http://www.w3.org/ns/dcat#accessURL": [{"@id": "https://example.org/files/a.csv"}],
    },
    {
        "@id": "https://example.org/organization/1",
        "@type": ["http://xmlns.com/foaf/0.1/Organization"],
        "http://xmlns.com/foaf/0.1/name": [{"@value": "Org One"}],
    },
]

_PAGE_2: list[dict[str, object]] = [
    {
        "@id": f"{_CATALOG_URL}?page=2",
        "@type": ["http://www.w3.org/ns/hydra/core#PagedCollection"],
        "http://www.w3.org/ns/hydra/core#totalItems": [{"@value": 2}],
    },
    {
        "@id": "https://example.org/dataset/2",
        "@type": ["http://www.w3.org/ns/dcat#Dataset"],
        "http://purl.org/dc/terms/title": [{"@value": "Dataset Two"}],
    },
]

_PAGES: dict[str, object] = {
    _CATALOG_URL: _PAGE_1,
    f"{_CATALOG_URL}?page=2": _PAGE_2,
}


def _http() -> NiceHttpClientConfig:
    return NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None)


def _config(url: str = _CATALOG_URL) -> Config:
    return Config.model_validate({
        "protocol": {
            "http": {"respect_robots_txt": False, "max_requests_per_second": None},
            "dcat_ap": {"entry_url": url},
        },
    })


def _type_config(url: str = _CATALOG_URL) -> DcatApProtocolConfig:
    return DcatApProtocolConfig(entry_url=url)


def _graph(result: object) -> Graph:
    assert isinstance(result, JsonLdDiscoveryResult)
    graph = Graph()
    graph.parse(data=json.dumps(result.payload), format="json-ld")
    return graph


def _transport_for(pages: dict[str, object]) -> httpx.MockTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        key = str(request.url)
        body = pages.get(key)
        if body is None:
            return httpx.Response(404, text="not found")
        return httpx.Response(200, content=json.dumps(body), headers={"content-type": "application/ld+json"})

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_dcat_ap_protocol_follows_hydra_pagination() -> None:
    transport = _transport_for(_PAGES)
    async with NiceHttpClient(_config().effective_protocol.http, transport=transport) as client:
        protocol = GenericPlugin.create_protocol(_config(), client=client)
        assert isinstance(protocol, DcatApProtocol)
        results = [result async for result in protocol.discover()]

    assert len(results) == 2
    assert all(isinstance(result, JsonLdDiscoveryResult) for result in results)
    assert [r.identifier for r in results] == [  # type: ignore[union-attr]
        "https://example.org/dataset/1",
        "https://example.org/dataset/2",
    ]


@pytest.mark.asyncio
async def test_dcat_ap_protocol_extracts_distribution_and_publisher_into_payload() -> None:
    transport = _transport_for(_PAGES)
    async with NiceHttpClient(_http(), transport=transport) as client:
        protocol = DcatApProtocol(_type_config(), client)
        results = [result async for result in protocol.discover()]

    first = _graph(results[0])
    titles = {str(o) for o in first.objects(None, DCTERMS.title)}
    assert titles == {"Dataset One", "File A"}
    names = {str(o) for o in first.objects(None, _FOAF.name)}
    assert names == {"Org One"}

    second_titles = {str(o) for o in _graph(results[1]).objects(None, DCTERMS.title)}
    assert second_titles == {"Dataset Two"}


@pytest.mark.asyncio
async def test_dcat_ap_protocol_expected_count_reads_hydra_total_items() -> None:
    transport = _transport_for(_PAGES)
    async with NiceHttpClient(_http(), transport=transport) as client:
        protocol = DcatApProtocol(_type_config(), client)
        assert await protocol.get_expected_count() == 2


@pytest.mark.asyncio
async def test_dcat_ap_protocol_raises_on_pagination_loop() -> None:
    looping_page = [
        {
            "@id": f"{_CATALOG_URL}?page=loop",
            "@type": ["http://www.w3.org/ns/hydra/core#PagedCollection"],
            "http://www.w3.org/ns/hydra/core#nextPage": [{"@value": _CATALOG_URL}],
        },
    ]
    transport = _transport_for({_CATALOG_URL: looping_page})
    async with NiceHttpClient(_http(), transport=transport) as client:
        protocol = DcatApProtocol(_type_config(), client)
        with pytest.raises(GenericProtocolError, match="pagination loop"):
            _ = [result async for result in protocol.discover()]


@pytest.mark.asyncio
async def test_dcat_ap_protocol_raises_on_invalid_jsonld() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content="not json-ld at all {{{", headers={"content-type": "application/ld+json"})

    transport = httpx.MockTransport(handler)
    async with NiceHttpClient(_http(), transport=transport) as client:
        protocol = DcatApProtocol(_type_config(), client)
        with pytest.raises(GenericProtocolError, match="Failed to fetch/parse"):
            _ = [result async for result in protocol.discover()]


@pytest.mark.asyncio
async def test_dcat_ap_protocol_payload_has_no_remote_context() -> None:
    transport = _transport_for(_PAGES)
    async with NiceHttpClient(_http(), transport=transport) as client:
        results = [result async for result in DcatApProtocol(_type_config(), client).discover()]

    first = results[0]
    assert isinstance(first, JsonLdDiscoveryResult)
    assert set(first.payload) == {"@graph"}
    assert "@context" not in json.dumps(first.payload)


def test_dcat_ap_nested_protocol() -> None:
    cfg = Config.model_validate({
        "protocol": {
            "http": {"respect_robots_txt": False, "max_requests_per_second": None},
            "dcat_ap": {"entry_url": _CATALOG_URL},
        },
    })
    assert cfg.active_protocol_type is ProtocolType.dcat_ap
    assert cfg.effective_protocol.dcat_ap is not None
    assert cfg.effective_protocol.dcat_ap.entry_url == _CATALOG_URL


@pytest.mark.asyncio
async def test_dcat_ap_protocol_honors_own_jsonld_threshold() -> None:
    type_config = DcatApProtocolConfig(entry_url=_CATALOG_URL, jsonld_parse_threshold_bytes=1)
    async with NiceHttpClient(_http()) as client:
        protocol = DcatApProtocol(type_config, client)
    assert protocol.config.jsonld_parse_threshold_bytes == 1

    cfg = Config.model_validate({
        "protocol": {
            "dcat_ap": {"entry_url": _CATALOG_URL, "jsonld_parse_threshold_bytes": 42},
        },
    })
    async with NiceHttpClient(_http()) as client:
        created = GenericPlugin.create_protocol(cfg, client=client)
    assert isinstance(created, DcatApProtocol)
    assert created.config.jsonld_parse_threshold_bytes == 42


@pytest.mark.asyncio
async def test_generic_plugin_harvests_dcat_ap_catalog_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """dcat_ap Protocol -> jsonld PayloadParser -> ckanext_dcat DataMapper through GenericPlugin.run()."""
    transport = _transport_for(_PAGES)

    def _client_factory(config: NiceHttpClientConfig) -> NiceHttpClient:
        return NiceHttpClient(config, transport=transport)

    monkeypatch.setattr(plugin_mod, "NiceHttpClient", _client_factory)
    plugin = GenericPlugin(
        _config(),
        MapperConfig.model_validate({"ckanext_dcat": {"catalog_name": "Example Catalog"}}),
        ParserConfig.model_validate({"jsonld": {}}),
    )

    results = [item async for item in plugin.run()]

    assert all(isinstance(item, HarvestedArc) for item in results), results
    assert sorted(item.identifier or "" for item in results if isinstance(item, HarvestedArc)) == [
        "example_org_dataset_1",
        "example_org_dataset_2",
    ]
