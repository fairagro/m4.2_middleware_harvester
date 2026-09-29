"""Mapper from DCAT-AP RDF graphs (e.g. CKAN ``ckanext-dcat`` output) to ARC RO-Crate JSON-LD.

Field access goes through StableGraph / ResourceView; ARC assembly stays here.
Nothing RDI-specific is hardcoded: catalog display name/URL come from
repository ``mapper:`` config (``catalog_name`` / ``catalog_url``), so the
same mapper serves any DCAT-AP RDI, not just SRADI.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import override

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
)
from arctrl.py.Core.ontology_source_reference import OntologySourceReference  # type: ignore[import-untyped]
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import DCTERMS
from rdflib.term import Node

from middleware.payload.harvested_arc import HarvestedArc
from middleware.payload.linked_data_mapper.linked_data_mapper import LinkedDataMapper, MappingContext
from middleware.payload.linked_data_mapper.stable_graph import ResourceView, StableGraph
from middleware.payload.mapper_config import MapperConfig, MapperType
from middleware.payload.person_contacts import require_nonempty_person_given_names

DCAT = Namespace("http://www.w3.org/ns/dcat#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

# ckanext-dcat carries some CKAN fields (e.g. "maintainer") through unparsed:
# the RDF literal value is CKAN's own raw JSON string, not a plain display
# name. Recognized keys are unwrapped into "Name <email>"; anything else is
# used verbatim.
_ORG_NAME_KEYS = ("maintainer_name", "author_name", "name")
_ORG_EMAIL_KEYS = ("maintainer_email", "author_email", "email")


def _present(values: Iterable[str | None]) -> list[str]:
    """Drop ``None``/empty entries from an optional-string iterable."""
    return [v for v in values if v]


@LinkedDataMapper.register(MapperType.dcat_ap_general)
class DcatApMapper(LinkedDataMapper):
    """Maps a DCAT-AP RDF graph (one ``dcat:Dataset`` per call) to ARC objects.

    RDF reads use the ``StableGraph`` passed into ``_map_graph`` (via a per-call
    ``_DcatApRun``); DCAT-AP ARC policy stays here.
    """

    def __init__(self, catalog_name: str | None = None, catalog_url: str | None = None) -> None:
        """Create a mapper with optional repository-configured catalog provenance."""
        self._catalog_name = catalog_name
        self._catalog_url = catalog_url

    @classmethod
    @override
    def from_config(cls, config: MapperConfig, *, resource_base_url: str | None = None) -> DcatApMapper:
        """Construct a mapper from repository mapper configuration."""
        _ = resource_base_url  # DCAT-AP subjects are already absolute IRIs; unused here.
        return cls(
            catalog_name=config.catalog_name,
            catalog_url=str(config.catalog_url) if config.catalog_url else None,
        )

    @override
    def _map_graph(self, graph: Graph, context: MappingContext, stable: StableGraph) -> list[HarvestedArc]:
        """Map an RDF graph to harvested ARCs with composition counts.

        Yields one HarvestedArc per ``dcat:Dataset`` entity in the graph (in
        practice always exactly one: ``DcatApSitemap`` extracts a
        single-dataset subgraph per discovery result).
        """
        _ = graph  # Access via ``stable`` (call-scoped wrap).
        _ = context  # Discovery context unused; the dataset IRI is the identity.
        subjects = stable.subjects_of_type(DCAT.Dataset)
        if not subjects:
            raise ValueError("Graph does not contain a dcat:Dataset entity")

        run = _DcatApRun(self, stable, self._catalog_name, self._catalog_url)
        return [HarvestedArc.from_arctrl(run.map_arc(subject.node)) for subject in subjects]


@dataclass(frozen=True)
class _DcatApRun:
    """One ``map_graph`` call: owns the StableGraph explicitly (not on the mapper)."""

    mapper: DcatApMapper
    stable: StableGraph
    catalog_name: str | None
    catalog_url: str | None

    def view(self, subject: Node) -> ResourceView:
        """ResourceView for ``subject`` on this call's StableGraph."""
        return self.stable.view(subject)

    def map_arc(self, subject: Node) -> ARC:
        title = self._title(subject)
        identifier = self._investigation_identifier(subject, title)

        investigation = self._map_investigation(subject, identifier=identifier, title=title)
        study = self._map_study(subject, identifier, title=title)
        investigation.AddStudy(study)
        assay = self._map_assay(subject, identifier, title=title)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)
        return ARC.from_arc_investigation(investigation)

    def _map_investigation(self, subject: Node, *, identifier: str, title: str) -> ArcInvestigation:
        description = self.view(subject).text(DCTERMS.description) or ""
        submission_date = self.view(subject).text(DCTERMS.issued) or ""

        inv = ArcInvestigation.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=submission_date,
        )
        # No Person-level creator in ckanext-dcat output today (only org-level
        # publisher/contactPoint) -- Contacts stays empty; call kept for parity
        # / future-proofing if a DCAT-AP source ever adds foaf:Agent creators.
        require_nonempty_person_given_names(inv)
        self._add_investigation_comments(inv, subject)
        self._add_ontology_sources(inv)
        return inv

    def _map_study(self, subject: Node, investigation_id: str, *, title: str) -> ArcStudy:
        description = self.view(subject).text(DCTERMS.description) or ""
        study = ArcStudy.create(
            identifier=f"{investigation_id}_study",
            title=title,
            description=description,
            submission_date=self.view(subject).text(DCTERMS.issued) or "",
        )
        study.AddTable(self._create_dataset_processing_table(subject))
        return study

    def _map_assay(self, subject: Node, investigation_id: str, *, title: str) -> ArcAssay:
        assay = ArcAssay.create(
            identifier=f"{investigation_id}_assay",
            title=title,
            measurement_type=OntologyAnnotation(name="Data Collection"),
            technology_type=OntologyAnnotation(name="Data Repository"),
        )
        assay.TechnologyPlatform = OntologyAnnotation(name="DCAT-AP Catalog")
        assay.AddTable(self._create_distribution_table(subject))
        return assay

    def _create_dataset_processing_table(self, subject: Node) -> ArcTable:
        table = ArcTable.init("Dataset Processing")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Raw Data")],
        )
        table.AddColumn(
            CompositeHeader.parameter(OntologyAnnotation(name="Processing Description")),
            [CompositeCell.term(OntologyAnnotation(name="Published dataset metadata harvested via DCAT-AP."))],
        )
        keywords = self.view(subject).texts(DCAT.keyword)
        if keywords:
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Keywords")),
                [CompositeCell.term(OntologyAnnotation(name=", ".join(keywords)))],
            )
        languages = self.view(subject).texts(DCTERMS.language)
        if languages:
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Language")),
                [CompositeCell.term(OntologyAnnotation(name="; ".join(languages)))],
            )
        table.AddColumn(
            CompositeHeader.output(IOType.data()),
            [CompositeCell.create_data_from_string("Published Dataset")],
        )
        return table

    def _create_distribution_table(self, subject: Node) -> ArcTable:
        distributions = self.view(subject).resources(DCAT.distribution)
        urls = _present(d.text(DCAT.accessURL) or d.text(DCAT.downloadURL) for d in distributions)
        output_uri = urls[0] if urls else str(subject)

        table = ArcTable.init("Measurement")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Dataset Source")],
        )
        table.AddColumn(
            CompositeHeader.output(IOType.of_string("URI")),
            [CompositeCell.free_text(output_uri)],
        )

        titles = _present(d.text(DCTERMS.title) for d in distributions)
        if titles:
            table.AddColumn(CompositeHeader.comment("Distribution Title"), [CompositeCell.free_text("; ".join(titles))])

        formats = _present(d.text(DCTERMS.format) for d in distributions)
        if formats:
            table.AddColumn(
                CompositeHeader.comment("Format"), [CompositeCell.free_text("; ".join(sorted(set(formats))))]
            )

        if urls:
            table.AddColumn(CompositeHeader.comment("Access URL"), [CompositeCell.free_text("; ".join(urls))])

        licenses = _present(d.text(DCTERMS.license) for d in distributions)
        if licenses:
            table.AddColumn(
                CompositeHeader.comment("License"), [CompositeCell.free_text("; ".join(sorted(set(licenses))))]
            )
        return table

    def _add_investigation_comments(self, inv: ArcInvestigation, subject: Node) -> None:
        view = self.view(subject)

        source_identifier = view.text(DCTERMS.identifier)
        if source_identifier:
            inv.Comments.append(Comment.create("Source Identifier", source_identifier))

        modified = view.text(DCTERMS.modified)
        if modified:
            inv.Comments.append(Comment.create("Modified", modified))

        keywords = view.texts(DCAT.keyword)
        if keywords:
            inv.Comments.append(Comment.create("Keywords", "; ".join(keywords)))

        languages = view.texts(DCTERMS.language)
        if languages:
            inv.Comments.append(Comment.create("Language", "; ".join(languages)))

        publisher = view.resource(DCTERMS.publisher)
        publisher_label = self._org_label(publisher, FOAF.name) if publisher else None
        if publisher_label:
            inv.Comments.append(Comment.create("Publisher", publisher_label))

        contact_point = view.resource(DCAT.contactPoint)
        contact_label = self._org_label(contact_point, VCARD.fn) if contact_point else None
        if contact_label:
            inv.Comments.append(Comment.create("Contact Point", contact_label))

        if view.resource(DCTERMS.spatial) is not None:
            inv.Comments.append(
                Comment.create("Spatial Extent", "Geographic extent provided by the source RDI (see the RDI record).")
            )

        catalog_value = self._catalog_comment_value()
        if catalog_value:
            inv.Comments.append(Comment.create("Data Catalog", catalog_value))

    @staticmethod
    def _add_ontology_sources(inv: ArcInvestigation) -> None:
        inv.OntologySourceReferences.append(
            OntologySourceReference.create(
                name="DCAT",
                file="http://www.w3.org/ns/dcat#",
                version="",
                description="Data Catalog Vocabulary (DCAT-AP)",
            )
        )

    def _catalog_comment_value(self) -> str | None:
        if self.catalog_name and self.catalog_url:
            return f"{self.catalog_name} ({self.catalog_url})"
        return self.catalog_name or self.catalog_url

    @classmethod
    def _org_label(cls, org: ResourceView, *name_predicates: URIRef) -> str | None:
        raw = org.text(*name_predicates)
        if not raw:
            return None
        return cls._clean_org_label(raw)

    @staticmethod
    def _clean_org_label(raw: str) -> str:
        """Unwrap ckanext-dcat's raw CKAN JSON-string org fields, else pass through.

        Some ckanext-dcat deployments serialize CKAN's raw ``maintainer``/
        ``author`` JSON string directly as the ``vcard:fn`` / ``foaf:name``
        literal instead of a plain display name -- either a bare object
        (``{"maintainer_name": "...", "maintainer_email": "..."}``) or,
        matching CKAN's own ``author``/``maintainer`` package fields, a
        single-element array of one (``[{"maintainer_name": "...", ...}]``).
        Recover a readable label when possible.
        """
        text = raw.strip()
        if not ((text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]"))):
            return text
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return text
        if isinstance(data, list):
            data = data[0] if len(data) == 1 and isinstance(data[0], dict) else None
        if not isinstance(data, dict):
            return text
        name = next((str(data[key]).strip() for key in _ORG_NAME_KEYS if data.get(key)), None)
        email = next((str(data[key]).strip() for key in _ORG_EMAIL_KEYS if data.get(key)), None)
        if name and email:
            return f"{name} <{email}>"
        return name or text

    def _title(self, subject: Node) -> str:
        return self.view(subject).text(DCTERMS.title) or "Untitled"

    def _investigation_identifier(self, subject: Node, title: str) -> str:
        slug = self.mapper.sanitize_identifier(str(subject))
        return slug or self.mapper.to_identifier_slug(title) or "untitled"
