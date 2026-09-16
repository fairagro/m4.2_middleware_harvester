"""Shared Schema.org mapper title-fallback unit tests (issue #164 restored as fail-closed)."""

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


@pytest.mark.parametrize(
    "payload",
    [
        OPENAGRAR_MISSING_NAME_WITH_HEADLINE,
        OPENAGRAR_MISSING_NAME_WITH_ALTERNATIVE_HEADLINE,
        OPENAGRAR_MISSING_NAME_NO_FALLBACK,
    ],
)
def test_missing_name_fails_closed_naming_only_schema_name(payload: str) -> None:
    with pytest.raises(ValueError, match=r"no usable title \(schema:name\)"):
        list(GeneralSchemaOrgMapper().map_graph(parse_jsonld(payload), NO_DISCOVERY))


def test_missing_name_fails_closed_even_with_html_title_context() -> None:
    context = MappingContext(html_title="Citation Title From Page")
    with pytest.raises(ValueError, match=r"no usable title \(schema:name\)"):
        list(GeneralSchemaOrgMapper().map_graph(parse_jsonld(OPENAGRAR_MISSING_NAME_NO_FALLBACK), context))
