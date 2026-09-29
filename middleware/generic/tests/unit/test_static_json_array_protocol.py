"""Unit tests for static JSON array Protocol discovery (single GET, no pagination)."""

from __future__ import annotations

import httpx
import pytest
from arctrl import ARC  # type: ignore[import-untyped]

import middleware.generic.plugin as plugin_mod
from middleware.generic.config import Config, ProtocolType
from middleware.generic.errors import GenericProtocolError
from middleware.generic.plugin import GenericPlugin
from middleware.generic.protocol.static_json_array import StaticJsonArrayProtocol
from middleware.harvester.errors import RecordProcessingError, SkippedRecord
from middleware.harvester.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.harvester.plugin_base import HarvestedArc
from middleware.parsing.discovery import JsonLdDiscoveryResult
from middleware.parsing.parser_config import ParserConfig
from middleware.parsing.parser_type import ParserType
from middleware.payload.linked_data_mapper import LinkedDataMapper
from middleware.payload.mapper_config import MapperConfig, MapperType

_ARRAY_URL = "https://example.org/genomes.json"


def _config(url: str = _ARRAY_URL) -> Config:
    return Config(
        protocol_type=ProtocolType.static_json_array,
        sitemap_url=url,
        http=NiceHttpClientConfig(respect_robots_txt=False, max_requests_per_second=None),
    )


def _transport_for(body: object) -> httpx.MockTransport:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    return httpx.MockTransport(handler)


async def _discover(body: object) -> list[object]:
    async with NiceHttpClient(_config().http, transport=_transport_for(body)) as client:
        return [result async for result in StaticJsonArrayProtocol(_config(), client).discover()]


@pytest.mark.asyncio
async def test_static_json_array_protocol_single_get_yields_one_result_per_element() -> None:
    records = [
        {"@id": "https://doi.org/10.1/a", "name": "A"},
        {"@id": "https://doi.org/10.1/b", "name": "B"},
    ]
    calls = {"n": 0}

    async def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=records)

    async with NiceHttpClient(_config().http, transport=httpx.MockTransport(handler)) as client:
        protocol = GenericPlugin.create_protocol(_config(), client=client)
        assert isinstance(protocol, StaticJsonArrayProtocol)
        results = [result async for result in protocol.discover()]

    assert calls["n"] == 1
    assert len(results) == 2
    assert all(isinstance(result, JsonLdDiscoveryResult) for result in results)
    first, second = results
    assert isinstance(first, JsonLdDiscoveryResult)
    assert isinstance(second, JsonLdDiscoveryResult)
    assert first.payload["name"] == "A"
    assert second.payload["name"] == "B"
    assert first.identifier != second.identifier
    assert first.identifier.startswith(f"{LinkedDataMapper.sanitize_identifier('https://doi.org/10.1/a')}:")
    assert first.harvest_source_id == first.identifier


@pytest.mark.asyncio
async def test_static_json_array_protocol_raises_on_non_array_payload() -> None:
    with pytest.raises(GenericProtocolError, match="JSON array"):
        await _discover({"records": []})


@pytest.mark.asyncio
async def test_static_json_array_protocol_raises_on_invalid_json() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    async with NiceHttpClient(_config().http, transport=httpx.MockTransport(handler)) as client:
        protocol = StaticJsonArrayProtocol(_config(), client)
        with pytest.raises(GenericProtocolError, match="Failed to fetch/parse"):
            _ = [result async for result in protocol.discover()]


@pytest.mark.asyncio
async def test_static_json_array_protocol_yields_failure_for_non_object_elements() -> None:
    results = await _discover(["not-an-object", 42, {"@id": "https://doi.org/10.1/ok", "name": "Ok"}])

    assert len(results) == 3
    assert isinstance(results[0], RecordProcessingError)
    assert results[0].record_id == "static_json_array:index=0"
    assert "str" in str(results[0])
    assert isinstance(results[1], RecordProcessingError)
    assert results[1].record_id == "static_json_array:index=1"
    assert "int" in str(results[1])
    assert isinstance(results[2], JsonLdDiscoveryResult)
    assert results[2].identifier.startswith(f"{LinkedDataMapper.sanitize_identifier('https://doi.org/10.1/ok')}:")


@pytest.mark.asyncio
async def test_static_json_array_protocol_distinct_records_sharing_doi_are_both_discovered() -> None:
    shared_doi = "https://doi.org/10.1038/shared"
    results = await _discover([
        {"@id": shared_doi, "name": "Species A genome"},
        {"@id": shared_doi, "name": "Species B genome"},
    ])

    assert len(results) == 2
    identifiers = [result.identifier for result in results if isinstance(result, JsonLdDiscoveryResult)]
    assert len(set(identifiers)) == 2
    assert all(
        identifier.startswith(f"{LinkedDataMapper.sanitize_identifier(shared_doi)}:") for identifier in identifiers
    )


@pytest.mark.asyncio
async def test_static_json_array_protocol_identical_records_are_deduplicated() -> None:
    record = {"@id": "https://doi.org/10.1/dup", "name": "Same"}
    results = await _discover([dict(record), dict(record)])

    assert len(results) == 2
    assert isinstance(results[0], JsonLdDiscoveryResult)
    assert isinstance(results[1], SkippedRecord)


@pytest.mark.asyncio
async def test_static_json_array_protocol_identifier_stable_across_reordering() -> None:
    record_a = {"@id": "https://doi.org/10.1/a", "name": "A"}
    record_b = {"@id": "https://doi.org/10.1/b", "name": "B"}

    forward = await _discover([record_a, record_b])
    backward = await _discover([record_b, record_a])

    assert {r.identifier for r in forward if isinstance(r, JsonLdDiscoveryResult)} == {
        r.identifier for r in backward if isinstance(r, JsonLdDiscoveryResult)
    }


@pytest.mark.asyncio
async def test_static_json_array_protocol_expected_count_returns_array_length() -> None:
    records = [{"@id": f"https://doi.org/10.1/{i}", "name": str(i)} for i in range(5)]
    async with NiceHttpClient(_config().http, transport=_transport_for(records)) as client:
        count = await StaticJsonArrayProtocol(_config(), client).get_expected_count()

    assert count == 5


@pytest.mark.asyncio
async def test_generic_plugin_static_json_array_keeps_shared_doi_records_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """static_json_array Protocol -> jsonld PayloadParser -> schema_org_general DataMapper.

    Regression for the PlabiPD genomes.json shape (fairagro/m4_rdi_portfolio#7): several
    records legitimately share a DOI (one paper describing multiple species' genomes). All
    must survive as distinct ARCs with distinct identifiers, while sharing the same
    Publication.DOI. Records use the remote ``http://schema.org`` context string, which the
    parser must resolve locally.
    """
    shared_doi = "10.1038/shared"
    records = [
        {
            "@context": "http://schema.org",
            "@type": "Dataset",
            "@id": f"https://doi.org/{shared_doi}",
            "identifier": shared_doi,
            "name": name,
        }
        for name in ("Species A genome", "Species B genome")
    ] + [
        {
            "@context": "http://schema.org",
            "@type": "Dataset",
            "@id": "https://doi.org/10.1038/unique",
            "identifier": "10.1038/unique",
            "name": "Species C genome",
        }
    ]
    transport = _transport_for(records)

    def _client_factory(config: NiceHttpClientConfig) -> NiceHttpClient:
        return NiceHttpClient(config, transport=transport)

    monkeypatch.setattr(plugin_mod, "NiceHttpClient", _client_factory)
    plugin = GenericPlugin(
        _config(),
        MapperConfig(type=MapperType.schema_org_general),
        ParserConfig(type=ParserType.jsonld),
    )

    results = [item async for item in plugin.run()]

    assert len(results) == 3
    assert all(isinstance(item, HarvestedArc) for item in results), results
    harvested = [item for item in results if isinstance(item, HarvestedArc)]
    assert len({item.identifier for item in harvested}) == 3

    dois = [pub.DOI for item in harvested for pub in ARC.from_rocrate_json_string(item.arc_json).Publications]
    assert dois.count(shared_doi) == 2
    assert "10.1038/unique" in dois
