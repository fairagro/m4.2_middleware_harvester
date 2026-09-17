"""Unit tests for shared DataMapper registry and PayloadKind contracts."""

from collections.abc import Iterable
from typing import ClassVar, override

import pytest
from pydantic import ValidationError
from rdflib import Graph

from middleware.payload.data_mapper import DataMapper
from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.kinds import PayloadKind
from middleware.payload.linked_data_mapper import LinkedDataMapper
from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.linked_data_mapper.regal_mapper import RegalMapper
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.parsed_payload import ParsedPayload


def test_payload_kind_rdf_graph_available() -> None:
    assert PayloadKind.rdf_graph == "rdf_graph"


def test_parsed_payload_rejects_empty_identifier() -> None:
    with pytest.raises(ValueError, match="identifier"):
        ParsedPayload(kind=PayloadKind.rdf_graph, value=Graph(), identifier="  ")


def test_registry_resolves_schema_org_and_regal() -> None:
    assert DataMapper.registry[MapperType.schema_org_general] is GeneralSchemaOrgMapper
    assert DataMapper.registry[MapperType.regal_general] is RegalMapper
    assert LinkedDataMapper.registered_class(MapperType.schema_org_general) is GeneralSchemaOrgMapper
    assert LinkedDataMapper.registry is DataMapper.registry


def test_registered_rdf_mappers_accept_rdf_graph() -> None:
    assert GeneralSchemaOrgMapper.accepts == PayloadKind.rdf_graph
    assert RegalMapper.accepts == PayloadKind.rdf_graph


def test_data_mapper_map_contract() -> None:
    class _Stub(DataMapper[object]):
        accepts: ClassVar[PayloadKind] = PayloadKind.rdf_graph

        @override
        def map(self, payload: ParsedPayload, context: object) -> Iterable[HarvestedArc]:
            _ = context
            return [HarvestedArc(arc_json=f"id:{payload.identifier}")]

    stub = _Stub()
    out = list(stub.map(ParsedPayload(kind=PayloadKind.rdf_graph, value=Graph(), identifier="x"), object()))
    assert out[0].arc_json == "id:x"


def test_regal_from_config_requires_base_url() -> None:
    with pytest.raises(ValueError, match="resource_base_url"):
        RegalMapper.from_config(MapperConfig(type=MapperType.regal_general))


def test_regal_from_config_uses_fallback() -> None:
    mapper = RegalMapper.from_config(
        MapperConfig(type=MapperType.regal_general),
        resource_base_url="https://example.org/resource",
    )
    assert mapper._resource_base_url == "https://example.org/resource/"


def test_mapper_config_resource_base_url_requires_http_scheme() -> None:
    cfg = MapperConfig.model_validate({
        "type": MapperType.regal_general,
        "resource_base_url": "https://example.org/resource",
    })
    assert cfg.normalize_resource_base_url() == "https://example.org/resource/"
    assert (
        MapperConfig.model_validate({"type": MapperType.regal_general, "resource_base_url": "  "}).resource_base_url
        is None
    )
    with pytest.raises(ValidationError):
        MapperConfig.model_validate({
            "type": MapperType.regal_general,
            "resource_base_url": "ftp://example.org/resource",
        })
    with pytest.raises(ValidationError):
        MapperConfig.model_validate({"type": MapperType.regal_general, "resource_base_url": "not-a-url"})
