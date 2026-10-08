"""Unit tests for shared DataMapper registry and PayloadKind contracts."""

import logging
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


@pytest.mark.parametrize(
    "fields",
    [
        {"catalog_name": "Example Catalog"},
        {"catalog_url": "https://catalog.example.org"},
        {"catalog_name": "Example Catalog", "catalog_url": "https://catalog.example.org"},
    ],
)
def test_mapper_config_catalog_fields_warn_deprecated(caplog: pytest.LogCaptureFixture, fields: dict[str, str]) -> None:
    with caplog.at_level(logging.WARNING):
        cfg = MapperConfig.model_validate({"type": MapperType.ckanext_dcat, **fields})
    assert cfg.catalog_name == fields.get("catalog_name")
    assert any("mapper.catalog_name / mapper.catalog_url are deprecated" in r.message for r in caplog.records)


@pytest.mark.parametrize("fields", [{}, {"catalog_name": "  ", "catalog_url": ""}])
def test_mapper_config_without_catalog_fields_does_not_warn(
    caplog: pytest.LogCaptureFixture, fields: dict[str, str]
) -> None:
    with caplog.at_level(logging.WARNING):
        MapperConfig.model_validate({"type": MapperType.ckanext_dcat, **fields})
    assert not any("catalog_url are deprecated" in r.message for r in caplog.records)
