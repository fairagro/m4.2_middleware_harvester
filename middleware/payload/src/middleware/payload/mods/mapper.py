"""Map ``ModsRecord`` to ARC Investigation / Study / Assay (metadata-only)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar, override

from arctrl import (  # type: ignore[import-untyped]
    ARC,
    ArcAssay,
    ArcInvestigation,
    ArcStudy,
    ArcTable,
    Comment,
    CompositeCell,
    CompositeHeader,
    IOType,
    OntologyAnnotation,
    Person,
    Publication,
)
from arctrl.py.license import License  # type: ignore[import-untyped]

from middleware.payload.arc_license import license_from_value
from middleware.payload.data_mapper import DataMapper
from middleware.payload.dois import normalize_doi
from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.identifiers import sanitize_identifier, to_identifier_slug
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.mapping_context import MappingContext
from middleware.payload.mods.models import ModsName, ModsRecord
from middleware.payload.parsed_payload import ParsedPayload
from middleware.payload.person_contacts import publication_authors, require_nonempty_person_given_names
from middleware.payload.person_names import split_display_name
from middleware.payload.placeholders import PlaceholderConfig


@DataMapper.register(MapperType.mods_general)
class ModsMapper(DataMapper[MappingContext]):
    """Map a typed MODS record to a metadata-only ARC (no data-file Outputs)."""

    accepts: ClassVar[PayloadKind] = PayloadKind.mods_record

    def __init__(self, placeholders: PlaceholderConfig | None = None) -> None:
        """Store placeholder config for licence / empty-value handling."""
        self._placeholders = placeholders or PlaceholderConfig()

    @classmethod
    @override
    def from_config(cls, config: MapperConfig, *, resource_base_url: str | None = None) -> ModsMapper:
        """Construct a MODS mapper from repository mapper configuration."""
        _ = resource_base_url
        return cls(config.placeholders)

    @override
    def map(self, payload: ParsedPayload, context: MappingContext) -> Iterable[HarvestedArc]:
        """Map ``mods_record`` payload using discovery context for id fallback."""
        if payload.kind != PayloadKind.mods_record:
            raise ValueError(f"ModsMapper accepts {PayloadKind.mods_record}, got {payload.kind}")
        if not isinstance(payload.value, ModsRecord):
            raise TypeError(f"mods_record value must be ModsRecord, got {type(payload.value)!r}")
        arc = self.map_record(payload.value, context)
        source = self._http_source_url(context.source_url)
        return (HarvestedArc.from_arctrl(arc, source_url=source),)

    def map_record(self, record: ModsRecord, context: MappingContext | None = None) -> ARC:
        """Build an ARC from a MODS intermediate record."""
        ctx = context or MappingContext()
        investigation = self._map_investigation(record, ctx)
        study = self._map_study(record)
        assay = self._map_assay(record, ctx)
        investigation.AddStudy(study)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)
        require_nonempty_person_given_names(investigation)
        license_ = self._license(record)
        return ARC.from_arc_investigation(investigation, license=license_)

    def _map_investigation(self, record: ModsRecord, context: MappingContext) -> ArcInvestigation:
        title = self._require_title(record)
        inv = ArcInvestigation.create(
            identifier=self.resolve_identifier(record, context),
            title=title,
            description=record.abstract,
            submission_date=record.date_issued,
            public_release_date=record.date_issued,
        )
        self._add_contacts(inv, record)
        self._add_publications(inv, record)
        self._add_investigation_comments(inv, record, context)
        return inv

    def _map_study(self, record: ModsRecord) -> ArcStudy:
        title = self._require_title(record)
        study = ArcStudy.create(
            identifier=self._slug_identifier(title, fallback="mods_study"),
            title=title,
            description=record.abstract,
        )
        keywords_table = self._create_keywords_table(record)
        if keywords_table is not None:
            study.AddTable(keywords_table)
        return study

    def _map_assay(self, record: ModsRecord, context: MappingContext) -> ArcAssay:
        title = self._require_title(record)
        assay = ArcAssay.create(
            identifier=self._slug_identifier(title, fallback="mods_assay"),
            title=title,
            measurement_type=OntologyAnnotation(name="Data Collection"),
            technology_type=OntologyAnnotation(name="Data Repository"),
        )
        assay.TechnologyPlatform = OntologyAnnotation(name="MODS")
        assay.AddTable(self._create_assay_table(record, context))
        return assay

    @staticmethod
    def _require_title(record: ModsRecord) -> str:
        if record.title and record.title.strip():
            return record.title.strip()
        raise ValueError("MODS record has no title")

    def resolve_identifier(self, record: ModsRecord, context: MappingContext) -> str:
        """Prefer DOI, then MyCoRe object id / harvest source id, then source URL."""
        doi = normalize_doi(record.doi)
        if doi:
            return self.sanitize_identifier(doi)
        object_id = (record.object_id or "").strip() or (context.harvest_source_id or "").strip()
        if object_id:
            return self.sanitize_identifier(object_id)
        source = self._http_source_url(context.source_url)
        if source:
            return self.sanitize_identifier(source)
        raise ValueError("MODS record has neither DOI, object id, nor source URL for Investigation.Identifier")

    @classmethod
    def sanitize_identifier(cls, raw: str) -> str:
        """Make *raw* safe for arctrl ``Investigation.identifier``."""
        return sanitize_identifier(raw)

    @staticmethod
    def _slug_identifier(title: str, *, fallback: str) -> str:
        slug = to_identifier_slug(title)
        return slug or fallback

    @staticmethod
    def _http_source_url(value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if text.startswith(("http://", "https://")):
            return text
        return None

    def _add_contacts(self, inv: ArcInvestigation, record: ModsRecord) -> None:
        for name in record.names:
            mapped = self._map_person(name)
            if mapped is not None:
                inv.Contacts.append(mapped)

    @staticmethod
    def _map_person(contact: ModsName) -> Person | None:
        given = (contact.given or "").strip() or None
        family = (contact.family or "").strip() or None
        if given is None or family is None:
            display = (contact.display_form or "").strip()
            if not display:
                return None
            parts = split_display_name(display)
            given = parts.given
            family = parts.family or family
        if given is None:
            raise ValueError(
                "Person contact must have a non-empty given name"
                + f" (last_name={family!r}, display_form={contact.display_form!r})"
            )
        comments: list[Comment] = []
        if contact.gnd and contact.gnd.strip():
            comments.append(Comment.create("GND", contact.gnd.strip()))
        orcid = (contact.orcid or "").strip() or None
        return Person.create(
            orcid=orcid,
            last_name=family or "",
            first_name=given,
            affiliation=contact.affiliation or "",
            comments=comments or None,
        )

    def _add_publications(self, inv: ArcInvestigation, record: ModsRecord) -> None:
        doi = normalize_doi(record.doi)
        if doi is None:
            return
        inv.Publications.append(
            Publication.create(
                title=self._require_title(record),
                authors=publication_authors(inv),
                doi=doi,
            )
        )

    def _add_investigation_comments(
        self,
        inv: ArcInvestigation,
        record: ModsRecord,
        context: MappingContext,
    ) -> None:
        source = self._http_source_url(context.source_url)
        if source:
            inv.Comments.append(Comment.create("Source URL", source))
        if record.language and record.language.strip():
            inv.Comments.append(Comment.create("Language", record.language.strip()))
        if record.license_uri and record.license_uri.strip():
            inv.Comments.append(Comment.create("License", record.license_uri.strip()))

    def _license(self, record: ModsRecord) -> License | None:
        return license_from_value(
            record.license_uri,
            placeholders=self._placeholders,
            name=record.license_label,
        )

    @staticmethod
    def _create_keywords_table(record: ModsRecord) -> ArcTable | None:
        if not record.keywords:
            return None
        table = ArcTable.init("Data Collection")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Research Subject")],
        )
        table.AddColumn(
            CompositeHeader.parameter(OntologyAnnotation(name="Keywords")),
            [CompositeCell.term(OntologyAnnotation(name=", ".join(record.keywords)))],
        )
        table.AddColumn(
            CompositeHeader.output(IOType.sample()),
            [CompositeCell.free_text("")],
        )
        return table

    def _create_assay_table(self, record: ModsRecord, context: MappingContext) -> ArcTable:
        """Annotation table: source URI + metadata comments — no data-file Outputs."""
        source = self._http_source_url(context.source_url) or ""
        table = ArcTable.init("Measurement")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Dataset Source")],
        )
        table.AddColumn(
            CompositeHeader.output(IOType.of_string("URI")),
            [CompositeCell.free_text(source)],
        )
        if record.license_uri and record.license_uri.strip():
            table.AddColumn(
                CompositeHeader.comment("License"),
                [CompositeCell.free_text(record.license_uri.strip())],
            )
        if record.datafile_names:
            table.AddColumn(
                CompositeHeader.comment("Datafile Name"),
                [CompositeCell.free_text("; ".join(record.datafile_names))],
            )
        return table
