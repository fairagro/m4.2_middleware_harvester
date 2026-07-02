"""Unit tests for Schema.org record filtering."""

from typing import TypedDict, Unpack

import pytest
from pydantic import ValidationError

from middleware.schema_org.config import Config, DatasetType, NiceHttpClientConfig, PayloadType, SitemapType
from middleware.schema_org.jsonld_dataset import extract_schema_org_dataset_dict, resolve_field_value
from middleware.schema_org.jsonld_types import SchemaOrgDatasetDict
from middleware.schema_org.record_filter import RecordFilter, RecordFilterConfig


class _MinimalConfigOverrides(TypedDict, total=False):
    record_filter: RecordFilterConfig | None


def _minimal_config(**overrides: Unpack[_MinimalConfigOverrides]) -> Config:
    return Config(
        sitemap_url="https://example.org/sitemap.xml",
        sitemap_type=SitemapType.xml,
        dataset_type=DatasetType.html_jsonld,
        payload_type=PayloadType.general,
        http=NiceHttpClientConfig(),
        **overrides,
    )


def test_record_filter_config_requires_field() -> None:
    with pytest.raises(ValidationError):
        RecordFilterConfig.model_validate({"include": "foo"})


def test_record_filter_config_requires_at_least_one_pattern() -> None:
    with pytest.raises(ValidationError, match="at least one of include or exclude"):
        RecordFilterConfig(field="publisher.name")


def test_record_filter_config_rejects_invalid_regex() -> None:
    with pytest.raises(ValidationError, match="Invalid regular expression"):
        RecordFilterConfig(field="publisher.name", include="[unclosed")


def test_record_filter_config_accepts_include_and_exclude() -> None:
    config = RecordFilterConfig(
        field="publisher.name",
        include="Thünen",
        exclude="Other",
    )
    assert config.include == "Thünen"
    assert config.exclude == "Other"


def test_config_accepts_optional_record_filter() -> None:
    config = _minimal_config()
    assert config.record_filter is None


def test_config_parses_record_filter() -> None:
    config = Config.model_validate(
        {
            "sitemap_url": "https://example.org/sitemap.xml",
            "sitemap_type": "xml",
            "dataset_type": "html_jsonld",
            "payload_type": "general",
            "http": {},
            "record_filter": {
                "field": "publisher.name",
                "exclude": "Thünen[- ]?Institut",
            },
        }
    )
    assert config.record_filter is not None
    assert config.record_filter.field == "publisher.name"


@pytest.mark.parametrize(
    ("dataset_dict", "field", "expected"),
    [
        ({"publisher": {"name": "Thünen-Institut"}}, "publisher.name", "Thünen-Institut"),
        ({"publisher": {"name": "  OpenAgrar  "}}, "publisher.name", "OpenAgrar"),
        ({"publisher": "not-a-dict"}, "publisher.name", None),
        ({"publisher": {"name": ""}}, "publisher.name", None),
        ({"publisher": {"name": ["", "First", "Second"]}}, "publisher.name", "First"),
        ({"count": 42}, "count", "42"),
        ({}, "publisher.name", None),
    ],
)
def test_resolve_field_value(dataset_dict: SchemaOrgDatasetDict, field: str, expected: str | None) -> None:
    assert resolve_field_value(dataset_dict, field) == expected


def test_extract_schema_org_dataset_dict_finds_first_dataset() -> None:
    blocks = [
        '{"@context": "https://schema.org", "@type": "Organization", "name": "Other"}',
        '{"@context": "https://schema.org", "@type": "Dataset", "name": "Target"}',
    ]
    dataset = extract_schema_org_dataset_dict(blocks)
    assert dataset["name"] == "Target"


def test_extract_schema_org_dataset_dict_raises_when_missing() -> None:
    with pytest.raises(ValueError, match="No Schema.org Dataset"):
        extract_schema_org_dataset_dict(['{"@type": "Organization"}'])


def test_record_filter_include_keeps_matching_value() -> None:
    record_filter = RecordFilter(RecordFilterConfig(field="publisher.name", include="Thünen"))
    assert record_filter.evaluate({"publisher": {"name": "Thünen-Institut"}}) is None


def test_record_filter_include_skips_non_matching_value() -> None:
    record_filter = RecordFilter(RecordFilterConfig(field="publisher.name", include="Thünen"))
    reason = record_filter.evaluate({"publisher": {"name": "OpenAgrar"}})
    assert reason is not None
    assert "field=publisher.name" in reason
    assert "include=Thünen" in reason
    assert "value=OpenAgrar" in reason


def test_record_filter_include_skips_missing_value() -> None:
    record_filter = RecordFilter(RecordFilterConfig(field="publisher.name", include="Thünen"))
    reason = record_filter.evaluate({})
    assert reason is not None
    assert "value=missing" in reason


def test_record_filter_exclude_skips_matching_value() -> None:
    record_filter = RecordFilter(RecordFilterConfig(field="publisher.name", exclude="Thünen"))
    reason = record_filter.evaluate({"publisher": {"name": "Thünen-Institut"}})
    assert reason is not None
    assert "exclude=Thünen" in reason
    assert "value=Thünen-Institut" in reason


def test_record_filter_exclude_keeps_non_matching_value() -> None:
    record_filter = RecordFilter(RecordFilterConfig(field="publisher.name", exclude="Thünen"))
    assert record_filter.evaluate({"publisher": {"name": "OpenAgrar"}}) is None


def test_record_filter_exclude_keeps_missing_value() -> None:
    record_filter = RecordFilter(RecordFilterConfig(field="publisher.name", exclude="Thünen"))
    assert record_filter.evaluate({}) is None


def test_record_filter_include_and_exclude_both_apply() -> None:
    record_filter = RecordFilter(
        RecordFilterConfig(
            field="publisher.name",
            include="Thünen",
            exclude="Atlas",
        )
    )
    assert record_filter.evaluate({"publisher": {"name": "Thünen-Institut"}}) is None
    assert record_filter.evaluate({"publisher": {"name": "Thünen-Atlas"}}) is not None
    assert record_filter.evaluate({"publisher": {"name": "OpenAgrar"}}) is not None


def test_record_filter_is_case_insensitive() -> None:
    record_filter = RecordFilter(RecordFilterConfig(field="publisher.name", include="thünen"))
    assert record_filter.evaluate({"publisher": {"name": "THÜNEN-INSTITUT"}}) is None
