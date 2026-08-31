"""Mapper from Regal ResearchData RDF graphs to ARC RO-Crate JSON-LD.

Field access goes through StableGraph / ResourceView; ARC assembly stays here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from urllib.parse import quote, urlparse

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
from arctrl.py.Core.ontology_source_reference import OntologySourceReference
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, SKOS
from rdflib.term import Node

from middleware.harvester.person_contacts import require_nonempty_person_given_names
from middleware.harvester.plugin_base import HarvestedArc

from ..config import Config, PayloadType
from .linked_data_mapper import LinkedDataMapper, MappingContext
from .stable_graph import LabelledNode, ResourceView, StableGraph

REGAL = Namespace("http://hbz-nrw.de/regal#")
DBO = Namespace("http://dbpedia.org/ontology/")
JOINED_FUNDING = URIRef("info:regal/regal/joinedFunding")
RESEARCH_DATA_TYPE = REGAL.ResearchData

# Predicates handled explicitly; remaining subject predicates become opaque comments.
_KNOWN_PREDICATES = {
    RDF.type,
    DCTERMS.title,
    DCTERMS.alternative,
    DCTERMS.description,
    DCTERMS.creator,
    DCTERMS.contributor,
    DCTERMS.subject,
    DCTERMS.language,
    DCTERMS.hasPart,
    DCTERMS.issued,
    DBO.institution,
    REGAL.doi,
    REGAL.yearOfCopyright,
    REGAL.ddc,
    REGAL.dataOrigin,
    REGAL.fundingId,
    REGAL.fundingProgram,
    REGAL.license,
    REGAL.contentType,
    REGAL.usageManual,
    REGAL.recordingCoordinates,
    REGAL.recordingLocation,
    REGAL.recordingPeriod,
    JOINED_FUNDING,
    SKOS.prefLabel,
    URIRef("http://hbz-nrw.de/regal#projectId"),
    URIRef("http://hbz-nrw.de/regal#accessScheme"),
    URIRef("http://hbz-nrw.de/regal#publishScheme"),
    URIRef("http://hbz-nrw.de/regal#embargoTime"),
    REGAL.catalogId,
    REGAL.itemID,
    REGAL.associatedPublication,
    # Structural contact-order metadata (docs/regal_mapping.md); not an opaque Comment.
    # TODO: when order keys are stable Literals/URIRefs, use them to sort Contacts.
    REGAL.contributorOrder,
}


@LinkedDataMapper.register(PayloadType.regal_general)
class RegalMapper(LinkedDataMapper):
    """Maps a Regal ResearchData RDF graph to ARC objects.

    RDF reads use the ``StableGraph`` passed into ``_map_graph`` (via a per-call
    ``_RegalRun``); Regal ARC policy stays here.
    """

    def __init__(self, resource_base_url: str) -> None:
        """Create a mapper that expands/strips Regal ids with ``resource_base_url``."""
        self._resource_base_url = resource_base_url.rstrip("/") + "/"

    @classmethod
    @override
    def from_config(cls, config: Config) -> RegalMapper:
        """Construct a mapper using ``config.effective_resource_base_url``."""
        return cls(config.effective_resource_base_url)

    @override
    def _stable_wrap(self, graph: Graph) -> StableGraph:
        """Wrap with ``skos:prefLabel`` as the Regal labelled-node policy."""
        return StableGraph.wrap(graph, label_predicates=(SKOS.prefLabel,))

    @override
    def _map_graph(self, graph: Graph, context: MappingContext, stable: StableGraph) -> list[HarvestedArc]:
        """Map an RDF graph to a harvested ARC with composition counts."""
        _ = context  # Discovery context unused for Regal Investigation.identifier.
        subject = self._find_research_data_subject(graph)
        if subject is None:
            raise ValueError("Graph does not contain a Regal ResearchData entity")

        arc = _RegalRun(self, stable, self._resource_base_url).map_arc(subject)
        return [HarvestedArc.from_arctrl(arc)]

    def _find_research_data_subject(self, graph: Graph) -> Node | None:
        subjects = list(graph.subjects(RDF.type, RESEARCH_DATA_TYPE))
        if subjects:
            return subjects[0]
        for subject in graph.subjects(REGAL.contentType, Literal("researchData")):
            return subject
        return None


@dataclass(frozen=True)
class _RegalRun:
    """One ``map_graph`` call: owns the StableGraph explicitly (not on the mapper)."""

    mapper: RegalMapper
    stable: StableGraph
    resource_base_url: str

    def view(self, subject: Node) -> ResourceView:
        """ResourceView for ``subject`` on this call's StableGraph."""
        return self.stable.view(subject)

    def map_arc(self, subject: Node) -> ARC:
        regal_id = self._regal_id(subject)
        doi = self._doi(subject)
        if not regal_id and not doi:
            raise ValueError("Regal record is missing both @id and doi")

        investigation = self._map_investigation(subject, regal_id=regal_id, doi=doi)
        study = self._map_study(subject, investigation.Identifier)
        investigation.AddStudy(study)
        assay = self._map_assay(subject, investigation.Identifier, regal_id=regal_id, doi=doi)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)
        return ARC.from_arc_investigation(investigation)

    def _map_investigation(
        self,
        subject: Node,
        *,
        regal_id: str | None,
        doi: str | None,
    ) -> ArcInvestigation:
        title = self._title(subject)
        identifier = self._investigation_identifier(regal_id=regal_id, doi=doi, title=title)
        description = self._join_texts(subject, DCTERMS.description)
        submission_date = self.view(subject).text(DCTERMS.issued) or ""

        inv = ArcInvestigation.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=submission_date,
        )
        institutions = self._labelled_pairs(subject, DBO.institution)
        affiliation = institutions[0][0] if len(institutions) == 1 else None
        self._add_contacts(inv, subject, affiliation=affiliation)
        require_nonempty_person_given_names(inv)
        self._add_publications(inv, subject, title=title, doi=doi)
        self._add_investigation_comments(inv, subject, institutions=institutions)
        self._add_ontology_sources(inv)
        return inv

    def _map_study(self, subject: Node, investigation_id: str) -> ArcStudy:
        title = self._title(subject)
        description = self._join_texts(subject, DCTERMS.description)
        usage_manual = self.view(subject).text(REGAL.usageManual)
        if usage_manual:
            description = f"{description}\n\nUsage Manual: {usage_manual}".strip()

        study = ArcStudy.create(
            identifier=f"{investigation_id}_study",
            title=title,
            description=description,
            submission_date=self.view(subject).text(DCTERMS.issued) or "",
        )

        spatial = self._create_spatial_sampling_table(subject)
        if spatial is not None:
            study.AddTable(spatial)

        collection = self._create_data_collection_table(subject)
        if collection is not None:
            study.AddTable(collection)

        study.AddTable(self._create_data_processing_table(subject))
        return study

    def _map_assay(
        self,
        subject: Node,
        investigation_id: str,
        *,
        regal_id: str | None,
        doi: str | None,
    ) -> ArcAssay:
        title = self._title(subject)
        assay = ArcAssay.create(
            identifier=f"{investigation_id}_assay",
            title=title,
            measurement_type=OntologyAnnotation(name="Data Collection"),
            technology_type=OntologyAnnotation(name="Data Repository"),
        )
        assay.TechnologyPlatform = OntologyAnnotation(name="Regal Research Data Repository")
        assay.AddTable(self._create_assay_table(subject, regal_id=regal_id, doi=doi))
        return assay

    def _create_spatial_sampling_table(self, subject: Node) -> ArcTable | None:
        locations = self._labelled_pairs(subject, REGAL.recordingLocation)
        coordinates = self.view(subject).texts(REGAL.recordingCoordinates)
        if not locations and not coordinates:
            return None

        table = ArcTable.init("Spatial Sampling")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Geographic Region")],
        )
        if locations:
            labels = ", ".join(label for label, _ in locations)
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Location")),
                [CompositeCell.term(OntologyAnnotation(name=labels))],
            )
        if coordinates:
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Coordinates")),
                [CompositeCell.term(OntologyAnnotation(name="; ".join(coordinates)))],
            )
        table.AddColumn(
            CompositeHeader.output(IOType.sample()),
            [CompositeCell.free_text("Selected Location(s)")],
        )
        return table

    def _create_data_collection_table(self, subject: Node) -> ArcTable | None:
        keywords = self._keyword_labels(subject)
        data_origins = self._labelled_pairs(subject, REGAL.dataOrigin)
        temporal = self.view(subject).text(REGAL.recordingPeriod)
        if not keywords and not data_origins and not temporal:
            return None

        table = ArcTable.init("Data Collection")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Research Subject")],
        )
        if keywords:
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Keywords")),
                [CompositeCell.term(OntologyAnnotation(name=", ".join(keywords)))],
            )
        if data_origins:
            labels = ", ".join(label for label, _ in data_origins)
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Data Origin")),
                [CompositeCell.term(OntologyAnnotation(name=labels))],
            )
        if temporal:
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Temporal Extent")),
                [CompositeCell.term(OntologyAnnotation(name=temporal))],
            )
        table.AddColumn(
            CompositeHeader.output(IOType.sample()),
            [CompositeCell.free_text("")],
        )
        return table

    def _create_data_processing_table(self, subject: Node) -> ArcTable:
        table = ArcTable.init("Data Processing")
        table.AddColumn(
            CompositeHeader.input(IOType.data()),
            [CompositeCell.create_data_from_string("Raw Data")],
        )
        table.AddColumn(
            CompositeHeader.parameter(OntologyAnnotation(name="Processing Description")),
            [CompositeCell.term(OntologyAnnotation(name="Published research data metadata from a Regal repository"))],
        )

        funders, programs, project_ids = self._funding_values(subject)
        if funders:
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Funder")),
                [CompositeCell.term(OntologyAnnotation(name="; ".join(funders)))],
            )
        if programs:
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Funding Program")),
                [CompositeCell.term(OntologyAnnotation(name="; ".join(programs)))],
            )
        if project_ids:
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="Project ID")),
                [CompositeCell.term(OntologyAnnotation(name="; ".join(project_ids)))],
            )

        license_value = self._license_value(subject)
        if license_value:
            table.AddColumn(
                CompositeHeader.parameter(OntologyAnnotation(name="License")),
                [CompositeCell.term(OntologyAnnotation(name=license_value))],
            )

        table.AddColumn(
            CompositeHeader.output(IOType.data()),
            [CompositeCell.create_data_from_string("Published Dataset")],
        )
        return table

    def _create_assay_table(
        self,
        subject: Node,
        *,
        regal_id: str | None,
        doi: str | None,
    ) -> ArcTable:
        output_uri = self._output_uri(regal_id=regal_id, doi=doi)
        table = ArcTable.init("Measurement")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Dataset Source")],
        )
        table.AddColumn(
            CompositeHeader.output(IOType.of_string("URI")),
            [CompositeCell.free_text(output_uri)],
        )

        license_value = self._license_value(subject)
        if license_value:
            table.AddColumn(CompositeHeader.comment("License"), [CompositeCell.free_text(license_value)])

        languages = self._labelled_pairs(subject, DCTERMS.language)
        if languages:
            labels = "; ".join(label for label, _ in languages)
            table.AddColumn(CompositeHeader.comment("Language"), [CompositeCell.free_text(labels)])

        parts = self._labelled_pairs(subject, DCTERMS.hasPart)
        if parts:
            urls = [self._resource_url(node_id) for _, node_id in parts if node_id]
            names = [label for label, _ in parts if label]
            if urls:
                table.AddColumn(
                    CompositeHeader.comment("Online Resource"),
                    [CompositeCell.free_text("; ".join(urls))],
                )
            if names:
                table.AddColumn(
                    CompositeHeader.comment("Online Resource Name"),
                    [CompositeCell.free_text("; ".join(names))],
                )

        institutions = self._labelled_pairs(subject, DBO.institution)
        if institutions:
            table.AddColumn(
                CompositeHeader.comment("Institution"),
                [CompositeCell.free_text("; ".join(label for label, _ in institutions))],
            )
        return table

    def _add_contacts(
        self,
        inv: ArcInvestigation,
        subject: Node,
        *,
        affiliation: str | None,
    ) -> None:
        view = self.view(subject)
        # Literals then resources, each in StableGraph order — never rdflib iteration order.
        for lit in view.literals(DCTERMS.creator):
            self._append_contact_from_label(inv, lit.value, "author", affiliation=affiliation, node_id=None)
        for res in view.resources(DCTERMS.creator):
            self._append_contact_from_resource(inv, res, "author", affiliation=affiliation)
        for lit in view.literals(DCTERMS.contributor):
            self._append_contact_from_label(inv, lit.value, "contributor", affiliation=affiliation, node_id=None)
        for res in view.resources(DCTERMS.contributor):
            self._append_contact_from_resource(inv, res, "contributor", affiliation=affiliation)

    def _append_contact_from_label(
        self,
        inv: ArcInvestigation,
        label: str,
        role: str,
        *,
        affiliation: str | None,
        node_id: str | None,
    ) -> None:
        person = self._person_from_label(
            inv,
            self._split_regal_agent_label(label),
            affiliation=affiliation,
            role=role,
            node_id=node_id,
        )
        if person is None:
            return
        person.Roles.append(OntologyAnnotation(name=role))
        inv.Contacts.append(person)

    def _append_contact_from_resource(
        self,
        inv: ArcInvestigation,
        res: ResourceView,
        role: str,
        *,
        affiliation: str | None,
    ) -> None:
        pref_label = res.text(SKOS.prefLabel) or ""
        if not pref_label:
            return
        self._append_contact_from_label(
            inv,
            pref_label,
            role,
            affiliation=affiliation,
            node_id=res.iri,
        )

    @staticmethod
    def _split_regal_agent_label(label: str) -> tuple[str, str]:
        """Split Regal agent labels on first ``", "`` → ``(family, given)``.

        PUBLISSO/Regal person ``prefLabel`` values use ``Family, Given`` form.
        Labels without ``", "`` are treated as organization/label agents (empty
        given → Comment path in ``_person_from_label``).
        """
        stripped = label.strip()
        if ", " not in stripped:
            return stripped, ""
        family, given = stripped.split(", ", 1)
        return family.strip(), given.strip()

    def _person_from_label(
        self,
        inv: ArcInvestigation,
        names: tuple[str, str],
        *,
        affiliation: str | None,
        role: str,
        node_id: str | None,
    ) -> Person | None:
        family, given = names[0].strip(), names[1].strip()
        if given:
            person = Person.create(last_name=family, first_name=given, affiliation=affiliation or "")
            if node_id and self._is_orcid_uri(node_id):
                person.Comments.append(Comment.create("ORCID", node_id))
            return person

        # Empty given name: Organization/label agent → Comment; person identity → fail closed.
        if node_id and self._is_orcid_uri(node_id):
            raise ValueError(f"Person contact must have a non-empty given name (last_name={family!r})")
        if not family:
            return None
        comment_name = "Creator" if role == "author" else role.capitalize()
        value = family if not node_id else f"{family} ({node_id})"
        inv.Comments.append(Comment.create(comment_name, value))
        return None

    @staticmethod
    def _is_orcid_uri(uri: str) -> bool:
        """Return True when ``uri`` has host ``orcid.org`` (or a subdomain)."""
        host = (urlparse(uri).hostname or "").lower()
        return host == "orcid.org" or host.endswith(".orcid.org")

    def _add_publications(
        self,
        inv: ArcInvestigation,
        subject: Node,
        *,
        title: str,
        doi: str | None,
    ) -> None:
        if doi:
            authors = [p for p in inv.Contacts if any(r.Name == "author" for r in p.Roles)]
            author_strs: list[str] = []
            for person in authors:
                if person.FirstName and person.LastName:
                    author_strs.append(f"{person.LastName}, {person.FirstName[0]}.")
                elif person.LastName:
                    author_strs.append(person.LastName)
            inv.Publications.append(
                Publication.create(
                    title=title,
                    authors="; ".join(author_strs) if author_strs else None,
                    doi=doi,
                )
            )

        associated = URIRef("http://hbz-nrw.de/regal#associatedPublication")
        for uri in self.view(subject).texts(associated):
            inv.Comments.append(Comment.create("Associated Publication", uri))

    def _add_investigation_comments(
        self,
        inv: ArcInvestigation,
        subject: Node,
        *,
        institutions: list[tuple[str, str | None]],
    ) -> None:
        self._add_simple_comments(inv, subject)
        self._add_keyword_comments(inv, subject)
        self._add_institution_comments(inv, institutions)
        self._add_oai_comments(inv, subject)
        self._add_opaque_comments(inv, subject)

    def _add_simple_comments(self, inv: ArcInvestigation, subject: Node) -> None:
        for label, predicate in [
            ("Alternative Title", DCTERMS.alternative),
            ("Copyright Year", REGAL.yearOfCopyright),
            ("Access Scheme", REGAL.accessScheme),
            ("Publish Scheme", REGAL.publishScheme),
            ("Embargo", REGAL.embargoTime),
            ("Content Type", REGAL.contentType),
            ("Catalog ID", URIRef("http://hbz-nrw.de/regal#catalogId")),
        ]:
            value = self._join_texts(subject, predicate)
            if value:
                inv.Comments.append(Comment.create(label, value))

        license_value = self._license_value(subject)
        if license_value:
            inv.Comments.append(Comment.create("License", license_value))

        languages = self._labelled_pairs(subject, DCTERMS.language)
        if languages:
            inv.Comments.append(Comment.create("Language", "; ".join(label for label, _ in languages)))

    def _add_keyword_comments(self, inv: ArcInvestigation, subject: Node) -> None:
        for label, node_id in self._labelled_pairs(subject, DCTERMS.subject):
            comment_name = f"keyword [{node_id}]" if node_id else "keyword"
            inv.Comments.append(Comment.create(comment_name, label))

        for label, node_id in self._labelled_pairs(subject, REGAL.ddc):
            comment_name = f"keyword [DDC:{node_id}]" if node_id else "keyword [DDC]"
            inv.Comments.append(Comment.create(comment_name, label))

    @staticmethod
    def _add_institution_comments(
        inv: ArcInvestigation,
        institutions: list[tuple[str, str | None]],
    ) -> None:
        if len(institutions) == 1:
            return
        for label, node_id in institutions:
            value = f"{label} ({node_id})" if node_id else label
            inv.Comments.append(Comment.create("Institution", value))

    def _add_oai_comments(self, inv: ArcInvestigation, subject: Node) -> None:
        for labelled in self._sorted_labelled(self.view(subject).labelled(URIRef("http://hbz-nrw.de/regal#itemID"))):
            inv.Comments.append(Comment.create("OAI Identifier", labelled.label.value))

    def _add_opaque_comments(self, inv: ArcInvestigation, subject: Node) -> None:
        graph = self.stable.graph
        opaque: list[tuple[str, str, str]] = []
        for predicate, obj in graph.predicate_objects(subject):
            if predicate in _KNOWN_PREDICATES:
                continue
            pred_name = str(predicate).rsplit("/", maxsplit=1)[-1].rsplit("#", maxsplit=1)[-1]
            text = self.stable.object_text(obj)
            if not text:
                continue
            opaque.append((str(predicate), pred_name, text))
        opaque.sort(key=lambda item: (item[0].casefold(), item[0], item[2].casefold(), item[2]))
        for _, pred_name, text in opaque:
            inv.Comments.append(Comment.create(pred_name, text))

    def _add_ontology_sources(self, inv: ArcInvestigation) -> None:
        inv.OntologySourceReferences.append(
            OntologySourceReference.create(
                name="REGAL",
                file="http://hbz-nrw.de/regal#",
                version="",
                description="hbz Regal vocabulary",
            )
        )
        inv.OntologySourceReferences.append(
            OntologySourceReference.create(
                name="DDC",
                file="https://www.oclc.org/en/dewey.html",
                version="",
                description="Dewey Decimal Classification",
            )
        )

    def _funding_values(self, subject: Node) -> tuple[list[str], list[str], list[str]]:
        funders: list[str] = []
        programs: list[str] = []
        project_ids: list[str] = []

        joined_nodes = self.view(subject).resources(JOINED_FUNDING)
        if joined_nodes:
            for node_view in joined_nodes:
                program = node_view.text(REGAL.fundingProgramJoined)
                if program:
                    programs.append(program)
                project_id = node_view.text(REGAL.projectIdJoined)
                if project_id:
                    project_ids.append(project_id)
                funding_joined = node_view.resource(REGAL.fundingJoined)
                if funding_joined is not None:
                    label = funding_joined.text(SKOS.prefLabel)
                    if label:
                        funders.append(label)
                    elif funding_joined.iri:
                        funders.append(funding_joined.iri)
            return funders, programs, project_ids

        for label, _ in self._labelled_pairs(subject, REGAL.fundingId):
            funders.append(label)
        programs.extend(self.view(subject).texts(REGAL.fundingProgram))
        project_ids.extend(self.view(subject).texts(REGAL.projectId))
        return funders, programs, project_ids

    def _keyword_labels(self, subject: Node) -> list[str]:
        labels = [label for label, _ in self._labelled_pairs(subject, DCTERMS.subject)]
        labels.extend(label for label, _ in self._labelled_pairs(subject, REGAL.ddc))
        return labels

    def _license_value(self, subject: Node) -> str | None:
        return self.view(subject).text(REGAL.license)

    def _title(self, subject: Node) -> str:
        title = self.view(subject).text(DCTERMS.title)
        if title:
            return title
        pref = self.view(subject).text(SKOS.prefLabel)
        return pref or "Untitled"

    def _doi(self, subject: Node) -> str | None:
        doi = self.view(subject).text(REGAL.doi)
        return doi.strip() if doi else None

    def _regal_id(self, subject: Node) -> str | None:
        if isinstance(subject, URIRef):
            value = str(subject)
            if value.startswith(self.resource_base_url):
                return value.removeprefix(self.resource_base_url)
            if value.startswith(("frl:", "edoweb:")):
                return value
        return None

    def _investigation_identifier(
        self,
        *,
        regal_id: str | None,
        doi: str | None,
        title: str,
    ) -> str:
        if regal_id:
            slug = self.mapper.sanitize_identifier(regal_id)
            return slug or self.mapper.to_identifier_slug(title) or "untitled"
        if doi:
            return doi
        return self.mapper.to_identifier_slug(title) or "untitled"

    def _output_uri(self, *, regal_id: str | None, doi: str | None) -> str:
        if doi:
            return f"https://doi.org/{doi}"
        if regal_id:
            return self._resource_url(regal_id)
        return "unknown"

    def _resource_url(self, regal_id: str) -> str:
        """Expand a compact Regal id to an absolute resource URL.

        Absolute ``http(s)`` IRIs (including values already under
        ``resource_base_url`` after JSON-LD expansion) are returned unchanged
        so callers such as ``hasPart`` do not double-prefix.
        """
        if regal_id.startswith(("http://", "https://")):
            return regal_id
        return f"{self.resource_base_url}{quote(regal_id, safe=':')}"

    def _join_texts(self, subject: Node, predicate: Node) -> str:
        return "\n\n".join(self.view(subject).texts(predicate))

    def _labelled_pairs(self, subject: Node, predicate: Node) -> list[tuple[str, str | None]]:
        labelled = self._sorted_labelled(self.view(subject).labelled(predicate))
        return [(item.label.value, item.stable_id) for item in labelled]

    @staticmethod
    def _sorted_labelled(items: list[LabelledNode]) -> list[LabelledNode]:
        return sorted(
            items,
            key=lambda item: (
                item.label.value.casefold(),
                item.label.value,
                (item.stable_id or "").casefold(),
                item.stable_id or "",
            ),
        )
