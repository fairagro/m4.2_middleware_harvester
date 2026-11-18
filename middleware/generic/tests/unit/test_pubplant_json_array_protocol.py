"""Unit tests for PubPlant JSON array Protocol discovery (single GET, no pagination)."""

from __future__ import annotations

import logging

import httpx
import pytest
from arctrl import ARC  # type: ignore[import-untyped]

import middleware.generic.plugin as plugin_mod
from middleware.contracts.errors import RecordProcessingError, SkippedRecord
from middleware.contracts.nice_http_client import NiceHttpClient, NiceHttpClientConfig
from middleware.contracts.plugin_base import HarvestedArc
from middleware.generic.config import Config
from middleware.generic.errors import GenericProtocolError
from middleware.generic.plugin import GenericPlugin
from middleware.generic.protocol.pubplant_json_array import (
    PubPlantJsonArrayProtocol,
    PubPlantJsonArrayProtocolConfig,
)
from middleware.parsing.discovery import JsonLdDiscoveryResult
from middleware.parsing.jsonld_context_loader import clear_context_document_cache
from middleware.parsing.parser_config import ParserConfig
from middleware.payload.linked_data_mapper import LinkedDataMapper
from middleware.payload.mapper_config import MapperConfig

_ARRAY_URL = "https://example.org/genomes.json"
_SCHEMA_ORG_CONTEXT = "http://schema.org"
_SCHEMA_ORG_DOC = {"@context": {"@vocab": "http://schema.org/"}}


@pytest.fixture(autouse=True)
def _clear_jsonld_context_cache() -> None:
    clear_context_document_cache()


def _config(url: str = _ARRAY_URL) -> Config:
    return Config.model_validate({
        "protocol": {
            "http": {"respect_robots_txt": False, "max_requests_per_second": None},
            "pubplant_json_array": {"entry_url": url},
        },
    })


def _type_config(config: Config) -> PubPlantJsonArrayProtocolConfig:
    type_config = config.effective_protocol.type_config
    assert isinstance(type_config, PubPlantJsonArrayProtocolConfig)
    return type_config


def _transport_for(body: object, *, context_url: str | None = None) -> httpx.MockTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        if context_url is not None and str(request.url) == context_url:
            return httpx.Response(200, json=_SCHEMA_ORG_DOC)
        return httpx.Response(200, json=body)

    return httpx.MockTransport(handler)


async def _discover(body: object) -> list[object]:
    config = _config()
    async with NiceHttpClient(config.effective_protocol.http, transport=_transport_for(body)) as client:
        return [result async for result in PubPlantJsonArrayProtocol(_type_config(config), client).discover()]


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_single_get_yields_one_result_per_element() -> None:
    records = [
        {"@id": "https://doi.org/10.1/a", "name": "A"},
        {"@id": "https://doi.org/10.1/b", "name": "B"},
    ]
    calls = {"n": 0}

    async def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=records)

    async with NiceHttpClient(_config().effective_protocol.http, transport=httpx.MockTransport(handler)) as client:
        protocol = GenericPlugin.create_protocol(_config(), client=client)
        assert isinstance(protocol, PubPlantJsonArrayProtocol)
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
async def test_pubplant_json_array_protocol_raises_on_non_array_payload() -> None:
    with pytest.raises(GenericProtocolError, match="JSON array"):
        await _discover({"records": []})


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_raises_on_invalid_json() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    async with NiceHttpClient(_config().effective_protocol.http, transport=httpx.MockTransport(handler)) as client:
        protocol = PubPlantJsonArrayProtocol(_type_config(_config()), client)
        with pytest.raises(GenericProtocolError, match="Failed to fetch/parse"):
            _ = [result async for result in protocol.discover()]


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_yields_failure_for_non_object_elements() -> None:
    results = await _discover(["not-an-object", 42, {"@id": "https://doi.org/10.1/ok", "name": "Ok"}])

    assert len(results) == 3
    assert isinstance(results[0], RecordProcessingError)
    assert results[0].record_id == "pubplant_json_array:index=0"
    assert "str" in str(results[0])
    assert isinstance(results[1], RecordProcessingError)
    assert results[1].record_id == "pubplant_json_array:index=1"
    assert "int" in str(results[1])
    assert isinstance(results[2], JsonLdDiscoveryResult)
    assert results[2].identifier.startswith(f"{LinkedDataMapper.sanitize_identifier('https://doi.org/10.1/ok')}:")


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_distinct_records_sharing_doi_are_both_discovered() -> None:
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
async def test_pubplant_json_array_protocol_identical_records_are_deduplicated() -> None:
    record = {"@id": "https://doi.org/10.1/dup", "name": "Same"}
    results = await _discover([dict(record), dict(record)])

    assert len(results) == 2
    assert isinstance(results[0], JsonLdDiscoveryResult)
    assert isinstance(results[1], SkippedRecord)


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_identifier_stable_across_reordering() -> None:
    record_a = {"@id": "https://doi.org/10.1/a", "name": "A"}
    record_b = {"@id": "https://doi.org/10.1/b", "name": "B"}

    forward = await _discover([record_a, record_b])
    backward = await _discover([record_b, record_a])

    assert {r.identifier for r in forward if isinstance(r, JsonLdDiscoveryResult)} == {
        r.identifier for r in backward if isinstance(r, JsonLdDiscoveryResult)
    }


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_expected_count_is_unknown_without_fetching() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=[])

    async with NiceHttpClient(_config().effective_protocol.http, transport=httpx.MockTransport(handler)) as client:
        count = await PubPlantJsonArrayProtocol(_type_config(_config()), client).get_expected_count()

    assert count is None
    assert not requests


@pytest.mark.asyncio
async def test_generic_plugin_pubplant_json_array_keeps_shared_doi_records_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """pubplant_json_array Protocol -> jsonld PayloadParser -> schema_org_general DataMapper.

    Regression for the PlabiPD genomes.json shape (fairagro/m4_rdi_portfolio#7): several
    records legitimately share a DOI (one paper describing multiple species' genomes). All
    must survive as distinct ARCs with distinct identifiers, while sharing the same
    Publication.DOI. Records use the remote ``http://schema.org`` context string.
    With ``allowed_context_url`` unset (legacy configs), the shared loader still
    fetches and caches that IRI (and emits a one-time warning).
    """
    shared_doi = "10.1038/shared"
    records = [
        {
            "@context": _SCHEMA_ORG_CONTEXT,
            "@type": "Dataset",
            "@id": f"https://doi.org/{shared_doi}",
            "identifier": shared_doi,
            "name": name,
        }
        for name in ("Species A genome", "Species B genome")
    ] + [
        {
            "@context": _SCHEMA_ORG_CONTEXT,
            "@type": "Dataset",
            "@id": "https://doi.org/10.1038/unique",
            "identifier": "10.1038/unique",
            "name": "Species C genome",
        }
    ]
    transport = _transport_for(records, context_url=_SCHEMA_ORG_CONTEXT)

    def _client_factory(config: NiceHttpClientConfig) -> NiceHttpClient:
        return NiceHttpClient(config, transport=transport)

    monkeypatch.setattr(plugin_mod, "NiceHttpClient", _client_factory)
    plugin = GenericPlugin(
        _config(),
        MapperConfig.model_validate({"schema_org_general": {}}),
        ParserConfig.model_validate({"jsonld": {}}),
    )

    results = [item async for item in plugin.run()]

    assert len(results) == 3
    assert all(isinstance(item, HarvestedArc) for item in results), results
    harvested = [item for item in results if isinstance(item, HarvestedArc)]
    assert len({item.identifier for item in harvested}) == 3

    dois = [pub.DOI for item in harvested for pub in ARC.from_rocrate_json_string(item.arc_json).Publications]
    assert dois.count(shared_doi) == 2
    assert "10.1038/unique" in dois


@pytest.mark.asyncio
async def test_generic_plugin_pubplant_json_array_harvests_record_with_whitespace_in_doi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stray space in the DOI (PlabiPD genomes.json) must not make the record fail."""
    records = [
        {
            "@context": _SCHEMA_ORG_CONTEXT,
            "@type": "Dataset",
            "@id": "https://doi.org/10.1038/ s41597-026-06582-z",
            "identifier": "10.1038/ s41597-026-06582-z",
            "name": "Species A genome",
        }
    ]
    transport = _transport_for(records, context_url=_SCHEMA_ORG_CONTEXT)

    def _client_factory(config: NiceHttpClientConfig) -> NiceHttpClient:
        return NiceHttpClient(config, transport=transport)

    monkeypatch.setattr(plugin_mod, "NiceHttpClient", _client_factory)
    plugin = GenericPlugin(
        _config(),
        MapperConfig.model_validate({"schema_org_general": {}}),
        ParserConfig.model_validate({"jsonld": {}}),
    )

    results = [item async for item in plugin.run()]

    assert len(results) == 1
    assert isinstance(results[0], HarvestedArc), results


@pytest.mark.asyncio
async def test_generic_plugin_pubplant_json_array_arc_carries_doi_without_whitespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = [
        {
            "@context": _SCHEMA_ORG_CONTEXT,
            "@type": "Dataset",
            "@id": "https://doi.org/10.1038/ s41597-026-06582-z",
            "identifier": "10.1038/ s41597-026-06582-z",
            "name": "Species A genome",
        }
    ]
    transport = _transport_for(records, context_url=_SCHEMA_ORG_CONTEXT)

    def _client_factory(config: NiceHttpClientConfig) -> NiceHttpClient:
        return NiceHttpClient(config, transport=transport)

    monkeypatch.setattr(plugin_mod, "NiceHttpClient", _client_factory)
    plugin = GenericPlugin(
        _config(),
        MapperConfig.model_validate({"schema_org_general": {}}),
        ParserConfig.model_validate({"jsonld": {}}),
    )

    results = [item async for item in plugin.run()]

    assert len(results) == 1
    assert isinstance(results[0], HarvestedArc), results
    dois = [pub.DOI for pub in ARC.from_rocrate_json_string(results[0].arc_json).Publications]
    assert dois == ["10.1038/s41597-026-06582-z"]


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_spaced_record_and_fixed_twin_share_identifier() -> None:
    def record(doi: str) -> dict[str, object]:
        return {"@id": f"https://doi.org/{doi}", "identifier": doi, "name": "Species A genome"}

    spaced = await _discover([record("10.1038/ s41597-026-06582-z")])
    fixed = await _discover([record("10.1038/s41597-026-06582-z")])

    assert isinstance(spaced[0], JsonLdDiscoveryResult)
    assert isinstance(fixed[0], JsonLdDiscoveryResult)
    assert spaced[0].identifier == fixed[0].identifier
    assert spaced[0].payload == fixed[0].payload


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_record_without_whitespace_keeps_identifier_and_payload() -> None:
    record = {
        "@id": "https://doi.org/10.1038/s41597-026-06582-z",
        "identifier": "10.1038/s41597-026-06582-z",
        "name": "Species A genome",
    }

    results = await _discover([dict(record)])

    assert len(results) == 1
    assert isinstance(results[0], JsonLdDiscoveryResult)
    # Pinned from the pre-fix implementation on main: existing ARCs must keep their identity.
    assert results[0].identifier == "doi_org_10_1038_s41597-026-06582-z:8013671013bd2823"
    assert results[0].payload == record


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_warns_once_per_repaired_record(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    clean = {"@id": "https://doi.org/10.1/clean", "identifier": "10.1/clean", "name": "Clean"}
    spaced = {"@id": "https://doi.org/10.1038/ s41597-026-06582-z", "identifier": "10.1038/ s41597-026-06582-z"}

    await _discover([clean, spaced])

    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "https://doi.org/10.1038/ s41597-026-06582-z" in warnings[0].getMessage()


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_keeps_free_text_identifier_unchanged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    record = {"@id": "https://example.org/genome/12", "identifier": "Genome Assembly 12", "name": "Species A genome"}

    results = await _discover([dict(record)])

    assert isinstance(results[0], JsonLdDiscoveryResult)
    assert results[0].payload == record
    assert not [entry for entry in caplog.records if entry.levelno == logging.WARNING]


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_removes_every_kind_of_whitespace() -> None:
    results = await _discover([
        {"@id": " https://doi.org/10.1038/\ts41597-\n026-06582-z ", "identifier": "10.1038/ s41597-026-06582-z\t"}
    ])

    assert isinstance(results[0], JsonLdDiscoveryResult)
    assert results[0].payload["@id"] == "https://doi.org/10.1038/s41597-026-06582-z"
    assert results[0].payload["identifier"] == "10.1038/s41597-026-06582-z"


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_repairs_spaced_identifier_when_id_is_clean(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)

    results = await _discover([
        {"@id": "https://doi.org/10.1038/s41597-026-06582-z", "identifier": "10.1038/ s41597-026-06582-z"}
    ])

    assert isinstance(results[0], JsonLdDiscoveryResult)
    assert results[0].payload["identifier"] == "10.1038/s41597-026-06582-z"
    assert len([entry for entry in caplog.records if entry.levelno == logging.WARNING]) == 1


@pytest.mark.asyncio
async def test_pubplant_json_array_protocol_warning_names_only_the_repaired_field(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)

    await _discover([{"@id": "https://doi.org/10.1038/s41597-026-06582-z", "identifier": "10.1038/ s41597-026-06582-z"}])

    message = next(entry for entry in caplog.records if entry.levelno == logging.WARNING).getMessage()
    assert "identifier='10.1038/ s41597-026-06582-z'" in message
    assert "@id" not in message
