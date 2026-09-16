"""OpenAgrar Schema.org mapper overlay (issue #164)."""

from __future__ import annotations

from typing import ClassVar, override

from ..config import PayloadType
from .general_schema_org_mapper import GeneralSchemaOrgMapper, ResolvedField
from .linked_data_mapper import LinkedDataMapper, MappingContext
from .stable_graph import ResourceView


@LinkedDataMapper.register_overlay("openagrar")
class OpenAgrarSchemaOrgMapper(GeneralSchemaOrgMapper):
    """OpenAgrar overlay: accepts a title fallback chain beyond ``schema:name``.

    OpenAgrar's Schema.org export omits ``schema:name`` on a minority of
    records (~13 of 910); the shared mapper fails closed on that (see
    ``GeneralSchemaOrgMapper``). This overlay tries, in order,
    ``schema:headline``, the first non-empty ``schema:alternativeHeadline``,
    then the HTML ``citation_title``/``<title>`` hint carried on
    ``MappingContext.html_title``.
    """

    BUILDS_ON: ClassVar[PayloadType | None] = PayloadType.schema_org_general
    TITLE_SOURCES: ClassVar[tuple[str, ...]] = (
        "schema:name",
        "headline",
        "alternativeHeadline",
        "html_title",
    )

    @override
    def resolve_title_fallback(self, dataset: ResourceView, context: MappingContext) -> ResolvedField | None:
        """Try headline, then the first non-empty alternativeHeadline, then the page-title hint."""
        headline = (dataset["headline"] or "").strip()
        if headline:
            return ResolvedField(headline, "headline")

        for alternative in dataset.schema_texts("alternativeHeadline"):
            alternative = alternative.strip()
            if alternative:
                return ResolvedField(alternative, "alternativeHeadline")

        html_title = (context.html_title or "").strip()
        if html_title:
            return ResolvedField(html_title, "html_title")

        return None
