"""Unit tests for shared DataMapper registry and PayloadKind contracts."""

from collections.abc import Iterable
from typing import ClassVar, override

import pytest
from pydantic import ValidationError
from rdflib import Graph

from middleware.payload.data_mapper import DataMapper
from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.inspire.mapper import InspireMapper
from middleware.payload.kinds import PayloadKind
from middleware.payload.linked_data_mapper import LinkedDataMapper
from middleware.payload.linked_data_mapper.general_schema_org_mapper import GeneralSchemaOrgMapper
from middleware.payload.linked_data_mapper.regal_mapper import RegalMapper
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.mapping_context import MappingContext
from middleware.payload.parsed_payload import ParsedPayload
from middleware.payload.phenoroam.mapper import PhenoroamMapper


def test_payload_kind_rdf_graph_available() -> None:
    assert PayloadKind.rdf_graph == "rdf_graph"
    assert PayloadKind.phenoroam_record == "phenoroam_record"


def test_payload_kind_inspire_record_available() -> None:
    assert PayloadKind.inspire_record == "inspire_record"


def test_parsed_payload_rejects_empty_identifier() -> None:
    with pytest.raises(ValueError, match="identifier"):
        ParsedPayload(kind=PayloadKind.rdf_graph, value=Graph(), identifier="  ")


def test_registry_resolves_schema_org_and_regal() -> None:
    assert DataMapper.registry[MapperType.schema_org_general] is GeneralSchemaOrgMapper
    assert DataMapper.registry[MapperType.regal_general] is RegalMapper
    assert LinkedDataMapper.registered_class(MapperType.schema_org_general) is GeneralSchemaOrgMapper
    assert LinkedDataMapper.registry is DataMapper.registry


def test_registry_resolves_inspire_general() -> None:
    assert DataMapper.registry[MapperType.inspire_general] is InspireMapper
    assert InspireMapper.accepts == PayloadKind.inspire_record


def test_registered_class_for_context_accepts_mapping_context_mappers() -> None:
    assert (
        DataMapper.registered_class_for_context(MapperType.schema_org_general, MappingContext) is GeneralSchemaOrgMapper
    )
    assert DataMapper.registered_class_for_context(MapperType.phenoroam_general, MappingContext) is PhenoroamMapper


def test_registered_class_for_context_rejects_incompatible_context() -> None:
    class _OtherContext:
        pass

    class _OtherMapper(DataMapper[_OtherContext]):
        accepts: ClassVar[PayloadKind] = PayloadKind.rdf_graph

        @override
        def map(self, payload: ParsedPayload, context: _OtherContext) -> Iterable[HarvestedArc]:
            _ = payload, context
            return []

    key = MapperType.schema_org_general
    previous = DataMapper.registry[key]
    DataMapper.registry[key] = _OtherMapper
    try:
        with pytest.raises(TypeError, match="expects context _OtherContext"):
            DataMapper.registered_class_for_context(key, MappingContext)
    finally:
        DataMapper.registry[key] = previous


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
        RegalMapper.from_config(MapperConfig.model_validate({"regal_general": {}}))


def test_regal_from_config_uses_fallback() -> None:
    mapper = RegalMapper.from_config(
        MapperConfig.model_validate({"regal_general": {}}),
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


def test_mapper_config_type_as_key_nested(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="middleware.payload.mapper_config"):
        cfg = MapperConfig.model_validate({
            "regal_general": {"resource_base_url": "https://example.org/resource"},
        })
    assert cfg.type == MapperType.regal_general
    assert cfg.normalize_resource_base_url() == "https://example.org/resource/"
    assert not any("mapper.type is deprecated" in r.message for r in caplog.records)


def test_mapper_config_legacy_type_warns_and_lifts(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING", logger="middleware.payload.mapper_config"):
        cfg = MapperConfig.model_validate({"type": "schema_org_general"})
    assert cfg.type == MapperType.schema_org_general
    assert cfg.schema_org_general is not None
    assert any("mapper.type is deprecated" in r.message for r in caplog.records)


def test_mapper_config_rejects_two_type_keys() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        MapperConfig.model_validate({"schema_org_general": {}, "inspire_general": {}})


def test_mapper_config_forbids_unknown_root_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        MapperConfig.model_validate({
            "regal_general": {},
            "resource_base_url": "https://example.org/resource/",
        })
