"""Map ``PhenoroamRecord`` to ARC Investigation / Study / Assay (metadata-only)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar, override
from urllib.parse import urlparse

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
)

from middleware.payload.data_mapper import DataMapper
from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.identifiers import sanitize_identifier, to_identifier_slug
from middleware.payload.kinds import PayloadKind
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.mapping_context import MappingContext
from middleware.payload.parsed_payload import ParsedPayload
from middleware.payload.person_contacts import require_nonempty_person_given_names
from middleware.payload.person_names import split_display_name
from middleware.payload.phenoroam.models import PhenoroamPerson, PhenoroamRecord

_LANDING_URL = "https://phenoroam.phenorob.de/geonetwork/srv/eng/catalog.search#/metadata/{id}"


@DataMapper.register(MapperType.phenoroam_general)
class PhenoroamMapper(DataMapper[MappingContext]):
    """Map a typed PhenoRoam record to a metadata-only ARC (no data-file Outputs)."""

    accepts: ClassVar[PayloadKind] = PayloadKind.phenoroam_record

    @classmethod
    @override
    def from_config(cls, config: MapperConfig, *, resource_base_url: str | None = None) -> PhenoroamMapper:
        """Construct a PhenoRoam mapper (no mapper-specific config fields)."""
        _ = config, resource_base_url
        return cls()

    @override
    def map(self, payload: ParsedPayload, context: MappingContext) -> Iterable[HarvestedArc]:
        """Map ``phenoroam_record`` payload using discovery context for id fallback."""
        if payload.kind != PayloadKind.phenoroam_record:
            raise ValueError(f"PhenoroamMapper accepts {PayloadKind.phenoroam_record}, got {payload.kind}")
        if not isinstance(payload.value, PhenoroamRecord):
            raise TypeError(f"phenoroam_record value must be PhenoroamRecord, got {type(payload.value)!r}")
        arc = self.map_record(payload.value, context)
        source = self._http_source_url(context.source_url)
        if source is None:
            catalog_id = self._catalog_id(payload.value, context)
            source = self._landing_url(catalog_id) if catalog_id else None
        # Return a tuple so kind/type guards run at call time (parity with LinkedDataMapper).
        return (HarvestedArc.from_arctrl(arc, source_url=source),)

    def map_record(self, record: PhenoroamRecord, context: MappingContext | None = None) -> ARC:
        """Build an ARC from a PhenoRoam intermediate record."""
        ctx = context or MappingContext()
        investigation = self._map_investigation(record, ctx)
        study = self._map_study(record)
        assay = self._map_assay(record, ctx)
        investigation.AddStudy(study)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)
        require_nonempty_person_given_names(investigation)
        return ARC.from_arc_investigation(investigation)

    def _map_investigation(self, record: PhenoroamRecord, context: MappingContext) -> ArcInvestigation:
        title = self._investigation_title(record)
        description = self._investigation_description(record)
        identifier = self.resolve_identifier(record, context)
        inv = ArcInvestigation.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=record.md_change_date,
        )
        self._add_contacts(inv, record)
        self._add_investigation_comments(inv, record, context)
        return inv

    def _map_study(self, record: PhenoroamRecord) -> ArcStudy:
        title = (record.study.study_title if record.study else None) or record.title or "PhenoRoam Study"
        description = (record.study.study_description if record.study else None) or record.description
        study = ArcStudy.create(
            identifier=self._slug_identifier(title, fallback="phenoroam_study"),
            title=title,
            description=description,
        )
        keywords_table = self._create_keywords_table(record)
        if keywords_table is not None:
            study.AddTable(keywords_table)
        return study

    def _map_assay(self, record: PhenoroamRecord, context: MappingContext) -> ArcAssay:
        title = record.title or self._investigation_title(record)
        assay = ArcAssay.create(
            identifier=self._slug_identifier(title, fallback="phenoroam_assay"),
            title=title,
            measurement_type=OntologyAnnotation(name="Data Collection"),
            technology_type=OntologyAnnotation(name="Data Repository"),
        )
        assay.TechnologyPlatform = OntologyAnnotation(name="PhenoRoam")
        assay.AddTable(self._create_assay_table(record, context))
        return assay

    @staticmethod
    def _investigation_title(record: PhenoroamRecord) -> str:
        if record.study and record.study.investigation_title and record.study.investigation_title.strip():
            return record.study.investigation_title.strip()
        if record.title and record.title.strip():
            return record.title.strip()
        raise ValueError("PhenoRoam record has no investigation or dataset title")

    @staticmethod
    def _investigation_description(record: PhenoroamRecord) -> str | None:
        if record.study and record.study.investigation_description:
            return record.study.investigation_description
        return record.description

    def resolve_identifier(self, record: PhenoroamRecord, context: MappingContext) -> str:
        """Prefer unique ``itemUUID``; otherwise a PhenoRoam landing-page URL."""
        uuid = (record.item_uuid or "").strip()
        if uuid:
            return self.sanitize_identifier(uuid)
        catalog_id = self._catalog_id(record, context)
        if not catalog_id:
            raise ValueError("PhenoRoam record has neither itemUUID nor catalog identifier for landing URL")
        return self.sanitize_identifier(self._landing_url(catalog_id))

    @staticmethod
    def _catalog_id(record: PhenoroamRecord, context: MappingContext) -> str:
        for candidate in (
            (record.item_uuid or "").strip(),
            (context.harvest_source_id or "").strip(),
        ):
            if candidate:
                return candidate
        return ""

    @staticmethod
    def _http_source_url(value: str | None) -> str | None:
        """Return an http(s) URL string, else ``None``."""
        if value is None:
            return None
        text = value.strip()
        if text.startswith(("http://", "https://")):
            return text
        return None

    @staticmethod
    def _landing_url(catalog_id: str) -> str:
        return _LANDING_URL.format(id=catalog_id)

    @classmethod
    def sanitize_identifier(cls, raw: str) -> str:
        """Make *raw* safe for arctrl ``Investigation.identifier`` (same policy as RDF mappers)."""
        return sanitize_identifier(raw)

    @staticmethod
    def _slug_identifier(title: str, *, fallback: str) -> str:
        slug = to_identifier_slug(title)
        return slug or fallback

    def _add_contacts(self, inv: ArcInvestigation, record: PhenoroamRecord) -> None:
        for person in (*record.responsible_contacts, *record.other_contacts):
            mapped = self._map_person(person)
            if mapped is not None:
                inv.Contacts.append(mapped)

    @staticmethod
    def _map_person(contact: PhenoroamPerson) -> Person | None:
        if not contact.name or not contact.name.strip():
            return None
        parts = split_display_name(contact.name)
        if parts.given is None:
            raise ValueError(
                "Person contact must have a non-empty given name"
                + f" (last_name={parts.family!r}, name={contact.name!r})"
            )
        return Person.create(
            last_name=parts.family,
            first_name=parts.given,
            email=contact.email,
            affiliation=contact.affiliation or "",
        )

    def _add_investigation_comments(
        self,
        inv: ArcInvestigation,
        record: PhenoroamRecord,
        context: MappingContext,
    ) -> None:
        catalog_id = self._catalog_id(record, context)
        if catalog_id:
            inv.Comments.append(Comment.create("Landing Page", self._landing_url(catalog_id)))
        if record.how_to_cite:
            inv.Comments.append(Comment.create("How To Cite", record.how_to_cite))
        if record.funded_by:
            inv.Comments.append(Comment.create("Funded By", record.funded_by))
        if record.download_information:
            inv.Comments.append(Comment.create("Download Information", record.download_information))
        for project in record.core_projects:
            if project.strip():
                inv.Comments.append(Comment.create("Core Project", project.strip()))
        thumb = self._valid_http_url(record.thumbnail_url)
        if thumb:
            inv.Comments.append(Comment.create("Thumbnail", thumb))

    @staticmethod
    def _create_keywords_table(record: PhenoroamRecord) -> ArcTable | None:
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

    def _create_assay_table(self, record: PhenoroamRecord, context: MappingContext) -> ArcTable:
        """Annotation table: landing URI + metadata comments — no data-file Outputs (#353)."""
        catalog_id = self._catalog_id(record, context)
        output_uri = self._landing_url(catalog_id) if catalog_id else ""

        table = ArcTable.init("Measurement")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Dataset Source")],
        )
        table.AddColumn(
            CompositeHeader.output(IOType.of_string("URI")),
            [CompositeCell.free_text(output_uri)],
        )
        if record.license_text and record.license_text.strip():
            # Keep comment compact for table cell readability.
            license_cell = " ".join(record.license_text.split())
            table.AddColumn(
                CompositeHeader.comment("License"),
                [CompositeCell.free_text(license_cell)],
            )
        valid_links = [link for link in record.datafile_links if self._valid_http_url(link)]
        if valid_links:
            table.AddColumn(
                CompositeHeader.comment("Datafile Link"),
                [CompositeCell.free_text(";".join(valid_links))],
            )
        if record.bbox is not None:
            bbox_bits = [
                f"W:{record.bbox.west}" if record.bbox.west else None,
                f"E:{record.bbox.east}" if record.bbox.east else None,
                f"S:{record.bbox.south}" if record.bbox.south else None,
                f"N:{record.bbox.north}" if record.bbox.north else None,
            ]
            bbox_text = " ".join(bit for bit in bbox_bits if bit)
            if bbox_text:
                table.AddColumn(
                    CompositeHeader.comment("Geographic Bounding Box"),
                    [CompositeCell.free_text(bbox_text)],
                )
        return table

    @staticmethod
    def _valid_http_url(value: str | None) -> str | None:
        """Return a usable http(s) URL, or None when missing/malformed.

        PhenoRoam often emits ``https://host:/path`` (empty port). Keep those: browsers and
        HTTP clients treat an empty port as the scheme default, and live fixtures use this
        shape on every datafile ``itemLink``.
        """
        if not value or not value.strip():
            return None
        candidate = value.strip()
        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"}:
            return None
        if not parsed.hostname:
            return None
        return candidate
