"""Schema.org mapper title-fallback unit tests (issue #164)."""

import logging

import pytest
from mapper_test_helpers import (
    NO_DISCOVERY,
    OPENAGRAR_MISSING_NAME_NO_FALLBACK,
    OPENAGRAR_MISSING_NAME_WITH_ALTERNATIVE_HEADLINE,
    OPENAGRAR_MISSING_NAME_WITH_HEADLINE,
    OPENAGRAR_PROPERTYVALUE_DOI,
    first_harvest,
    parse_jsonld,
    root_title,
    title_source_comment_text,
)

from middleware.linked_data.linked_data_mapper import GeneralSchemaOrgMapper, MappingContext


def test_schema_name_present_no_fallback_used() -> None:
    harvested = first_harvest(
        GeneralSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_PROPERTYVALUE_DOI), NO_DISCOVERY)
    )
    assert root_title(harvested.arc_json) == "Flower visitors in legume-intercrops"
    assert title_source_comment_text(harvested.arc_json) is None


def test_headline_fallback_used_when_name_missing(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        harvested = first_harvest(
            GeneralSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_MISSING_NAME_WITH_HEADLINE), NO_DISCOVERY)
        )
    assert root_title(harvested.arc_json) == "Flower visitors in legume-intercrops"
    assert title_source_comment_text(harvested.arc_json) == "headline"
    assert any("headline" in record.message for record in caplog.records)
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_alternative_headline_first_non_empty_used() -> None:
    harvested = first_harvest(
        GeneralSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_MISSING_NAME_WITH_ALTERNATIVE_HEADLINE), NO_DISCOVERY)
    )
    assert root_title(harvested.arc_json) == "Flower visitors in legume-intercrops"
    assert title_source_comment_text(harvested.arc_json) == "alternativeHeadline"


def test_html_title_fallback_used_when_context_supplies_it() -> None:
    context = MappingContext(html_title="Citation Title From Page")
    harvested = first_harvest(
        GeneralSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_MISSING_NAME_NO_FALLBACK), context)
    )
    assert root_title(harvested.arc_json) == "Citation Title From Page"
    assert title_source_comment_text(harvested.arc_json) == "html_title"


def test_no_fallback_available_fails_closed_without_untitled() -> None:
    with pytest.raises(ValueError, match="no usable title"):
        list(GeneralSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_MISSING_NAME_NO_FALLBACK), NO_DISCOVERY))
