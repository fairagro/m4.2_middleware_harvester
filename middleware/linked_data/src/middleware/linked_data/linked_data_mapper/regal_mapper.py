"""Mapper from Regal ResearchData RDF graphs to ARC RO-Crate JSON-LD."""

from __future__ import annotations

import re
from typing import cast
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

from ..config import Config, PayloadType
from .linked_data_mapper import LinkedDataMapper

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
}


@LinkedDataMapper.register(PayloadType.regal_general)
class RegalMapper(LinkedDataMapper):
    """Maps a Regal ResearchData RDF graph to ARC objects."""

    def __init__(self, resource_base_url: str) -> None:
        """Create a mapper that expands/strips Regal ids with ``resource_base_url``."""
        self._resource_base_url = resource_base_url.rstrip("/") + "/"

    @classmethod
    def from_config(cls, config: Config) -> RegalMapper:
        """Construct a mapper using ``config.effective_resource_base_url``."""
        return cls(config.effective_resource_base_url)

    def map_graph(self, graph: Graph) -> str:
        """Map an RDF graph to a serialized RO-Crate JSON-LD string."""
        subject = self._find_research_data_subject(graph)
        if subject is None:
            raise ValueError("Graph does not contain a Regal ResearchData entity")

        regal_id = self._regal_id(subject)
        doi = self._doi(graph, subject)
        if not regal_id and not doi:
            raise ValueError("Regal record is missing both @id and doi")

        arc = self._map_arc(graph, subject, regal_id=regal_id, doi=doi)
        return cast(str, arc.ToROCrateJsonString())

    def _find_research_data_subject(self, graph: Graph) -> Node | None:
        subjects = list(graph.subjects(RDF.type, RESEARCH_DATA_TYPE))
        if subjects:
            return subjects[0]
        for subject in graph.subjects(REGAL.contentType, Literal("researchData")):
            return subject
        return None

    def _map_arc(
        self,
        graph: Graph,
        subject: Node,
        *,
        regal_id: str | None,
        doi: str | None,
    ) -> ARC:
        investigation = self._map_investigation(graph, subject, regal_id=regal_id, doi=doi)
        study = self._map_study(graph, subject, investigation.Identifier)
        investigation.AddStudy(study)
        assay = self._map_assay(graph, subject, investigation.Identifier, regal_id=regal_id, doi=doi)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)
        return ARC.from_arc_investigation(investigation)

    def _map_investigation(
        self,
        graph: Graph,
        subject: Node,
        *,
        regal_id: str | None,
        doi: str | None,
    ) -> ArcInvestigation:
        title = self._title(graph, subject)
        identifier = self._investigation_identifier(regal_id=regal_id, doi=doi, title=title)
        description = self._join_literals(graph, subject, DCTERMS.description)
        submission_date = self._str(graph, subject, DCTERMS.issued) or ""

        inv = ArcInvestigation.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=submission_date,
        )
        institutions = self._labelled_nodes(graph, subject, DBO.institution)
        affiliation = institutions[0][0] if len(institutions) == 1 else None
        self._add_contacts(inv, graph, subject, affiliation=affiliation)
        self._add_publications(inv, graph, subject, title=title, doi=doi)
        self._add_investigation_comments(inv, graph, subject, institutions=institutions)
        self._add_ontology_sources(inv)
        return inv

    def _map_study(self, graph: Graph, subject: Node, investigation_id: str) -> ArcStudy:
        title = self._title(graph, subject)
        description = self._join_literals(graph, subject, DCTERMS.description)
        usage_manual = self._str(graph, subject, REGAL.usageManual)
        if usage_manual:
            description = f"{description}\n\nUsage Manual: {usage_manual}".strip()

        study = ArcStudy.create(
            identifier=f"{investigation_id}_study",
            title=title,
            description=description,
            submission_date=self._str(graph, subject, DCTERMS.issued) or "",
        )

        spatial = self._create_spatial_sampling_table(graph, subject)
        if spatial is not None:
            study.AddTable(spatial)

        collection = self._create_data_collection_table(graph, subject)
        if collection is not None:
            study.AddTable(collection)

        study.AddTable(self._create_data_processing_table(graph, subject))
        return study

    def _map_assay(
        self,
        graph: Graph,
        subject: Node,
        investigation_id: str,
        *,
        regal_id: str | None,
        doi: str | None,
    ) -> ArcAssay:
        title = self._title(graph, subject)
        assay = ArcAssay.create(
            identifier=f"{investigation_id}_assay",
            title=title,
            measurement_type=OntologyAnnotation(name="Data Collection"),
            technology_type=OntologyAnnotation(name="Data Repository"),
        )
        assay.TechnologyPlatform = OntologyAnnotation(name="Regal Research Data Repository")
        assay.AddTable(self._create_assay_table(graph, subject, regal_id=regal_id, doi=doi))
        return assay

    def _create_spatial_sampling_table(self, graph: Graph, subject: Node) -> ArcTable | None:
        locations = self._labelled_nodes(graph, subject, REGAL.recordingLocation)
        coordinates = [str(obj) for obj in graph.objects(subject, REGAL.recordingCoordinates) if obj is not None]
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

    def _create_data_collection_table(self, graph: Graph, subject: Node) -> ArcTable | None:
        keywords = self._keyword_labels(graph, subject)
        data_origins = self._labelled_nodes(graph, subject, REGAL.dataOrigin)
        temporal = self._str(graph, subject, REGAL.recordingPeriod)
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

    def _create_data_processing_table(self, graph: Graph, subject: Node) -> ArcTable:
        table = ArcTable.init("Data Processing")
        table.AddColumn(
            CompositeHeader.input(IOType.data()),
            [CompositeCell.create_data_from_string("Raw Data")],
        )
        table.AddColumn(
            CompositeHeader.parameter(OntologyAnnotation(name="Processing Description")),
            [CompositeCell.term(OntologyAnnotation(name="Published research data metadata from a Regal repository"))],
        )

        funders, programs, project_ids = self._funding_values(graph, subject)
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

        license_value = self._license_value(graph, subject)
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
        graph: Graph,
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

        license_value = self._license_value(graph, subject)
        if license_value:
            table.AddColumn(CompositeHeader.comment("License"), [CompositeCell.free_text(license_value)])

        languages = self._labelled_nodes(graph, subject, DCTERMS.language)
        if languages:
            labels = "; ".join(label for label, _ in languages)
            table.AddColumn(CompositeHeader.comment("Language"), [CompositeCell.free_text(labels)])

        parts = self._labelled_nodes(graph, subject, DCTERMS.hasPart)
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

        institutions = self._labelled_nodes(graph, subject, DBO.institution)
        if institutions:
            table.AddColumn(
                CompositeHeader.comment("Institution"),
                [CompositeCell.free_text("; ".join(label for label, _ in institutions))],
            )
        return table

    def _add_contacts(
        self,
        inv: ArcInvestigation,
        graph: Graph,
        subject: Node,
        *,
        affiliation: str | None,
    ) -> None:
        for node in graph.objects(subject, DCTERMS.creator):
            self._append_contact(inv, graph, node, "author", affiliation=affiliation)
        for node in graph.objects(subject, DCTERMS.contributor):
            self._append_contact(inv, graph, node, "contributor", affiliation=affiliation)

    def _append_contact(
        self,
        inv: ArcInvestigation,
        graph: Graph,
        node: Node,
        role: str,
        *,
        affiliation: str | None,
    ) -> None:
        person = self._node_to_person(graph, node, affiliation=affiliation)
        if person is None:
            return
        person.Roles.append(OntologyAnnotation(name=role))
        inv.Contacts.append(person)

    def _node_to_person(
        self,
        graph: Graph,
        node: Node,
        *,
        affiliation: str | None,
    ) -> Person | None:
        if isinstance(node, Literal):
            family, given = self._split_pref_label(str(node))
            return Person.create(last_name=family, first_name=given, affiliation=affiliation or "")

        pref_label = self._str(graph, node, SKOS.prefLabel) or ""
        if not pref_label:
            return None
        family, given = self._split_pref_label(pref_label)
        person = Person.create(last_name=family, first_name=given, affiliation=affiliation or "")
        node_id = str(node)
        if self._is_orcid_uri(node_id):
            person.Comments.append(Comment.create("ORCID", node_id))
        return person

    @staticmethod
    def _is_orcid_uri(uri: str) -> bool:
        """Return True when ``uri`` has host ``orcid.org`` (or a subdomain)."""
        host = (urlparse(uri).hostname or "").lower()
        return host == "orcid.org" or host.endswith(".orcid.org")

    def _add_publications(
        self,
        inv: ArcInvestigation,
        graph: Graph,
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

        for associated in graph.objects(subject, URIRef("http://hbz-nrw.de/regal#associatedPublication")):
            uri = str(associated)
            inv.Comments.append(Comment.create("Associated Publication", uri))

    def _add_investigation_comments(
        self,
        inv: ArcInvestigation,
        graph: Graph,
        subject: Node,
        *,
        institutions: list[tuple[str, str | None]],
    ) -> None:
        self._add_simple_comments(inv, graph, subject)
        self._add_keyword_comments(inv, graph, subject)
        self._add_institution_comments(inv, institutions)
        self._add_oai_comments(inv, graph, subject)
        self._add_opaque_comments(inv, graph, subject)

    def _add_simple_comments(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        for label, predicate in [
            ("Alternative Title", DCTERMS.alternative),
            ("Copyright Year", REGAL.yearOfCopyright),
            ("Access Scheme", REGAL.accessScheme),
            ("Publish Scheme", REGAL.publishScheme),
            ("Embargo", REGAL.embargoTime),
            ("Content Type", REGAL.contentType),
            ("Catalog ID", URIRef("http://hbz-nrw.de/regal#catalogId")),
        ]:
            value = self._join_literals(graph, subject, predicate)
            if value:
                inv.Comments.append(Comment.create(label, value))

        license_value = self._license_value(graph, subject)
        if license_value:
            inv.Comments.append(Comment.create("License", license_value))

        languages = self._labelled_nodes(graph, subject, DCTERMS.language)
        if languages:
            inv.Comments.append(Comment.create("Language", "; ".join(label for label, _ in languages)))

    def _add_keyword_comments(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        for label, node_id in self._labelled_nodes(graph, subject, DCTERMS.subject):
            comment_name = f"keyword [{node_id}]" if node_id else "keyword"
            inv.Comments.append(Comment.create(comment_name, label))

        for label, node_id in self._labelled_nodes(graph, subject, REGAL.ddc):
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

    def _add_oai_comments(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        for item in graph.objects(subject, URIRef("http://hbz-nrw.de/regal#itemID")):
            if isinstance(item, Literal):
                inv.Comments.append(Comment.create("OAI Identifier", str(item)))
            else:
                pref = self._str(graph, item, SKOS.prefLabel) or str(item)
                inv.Comments.append(Comment.create("OAI Identifier", pref))

    def _add_opaque_comments(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        for predicate, obj in graph.predicate_objects(subject):
            if predicate in _KNOWN_PREDICATES:
                continue
            pred_name = str(predicate).rsplit("/", maxsplit=1)[-1].rsplit("#", maxsplit=1)[-1]
            if isinstance(obj, Literal):
                inv.Comments.append(Comment.create(pred_name, str(obj)))
            else:
                pref = self._str(graph, obj, SKOS.prefLabel)
                inv.Comments.append(Comment.create(pred_name, pref or str(obj)))

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

    def _funding_values(
        self,
        graph: Graph,
        subject: Node,
    ) -> tuple[list[str], list[str], list[str]]:
        funders: list[str] = []
        programs: list[str] = []
        project_ids: list[str] = []

        joined_nodes = list(graph.objects(subject, JOINED_FUNDING))
        if joined_nodes:
            for node in joined_nodes:
                if isinstance(node, Literal):
                    continue
                program = self._str(graph, node, REGAL.fundingProgramJoined)
                if program:
                    programs.append(program)
                project_id = self._str(graph, node, REGAL.projectIdJoined)
                if project_id:
                    project_ids.append(project_id)
                funding_joined = graph.value(node, REGAL.fundingJoined)
                if funding_joined is not None and not isinstance(funding_joined, Literal):
                    label = self._str(graph, funding_joined, SKOS.prefLabel) or str(funding_joined)
                    funders.append(label)
            return funders, programs, project_ids

        for label, _ in self._labelled_nodes(graph, subject, REGAL.fundingId):
            funders.append(label)
        programs.extend(self._strs(graph, subject, REGAL.fundingProgram))
        project_ids.extend(self._strs(graph, subject, REGAL.projectId))
        return funders, programs, project_ids

    def _keyword_labels(self, graph: Graph, subject: Node) -> list[str]:
        labels = [label for label, _ in self._labelled_nodes(graph, subject, DCTERMS.subject)]
        labels.extend(label for label, _ in self._labelled_nodes(graph, subject, REGAL.ddc))
        return labels

    def _license_value(self, graph: Graph, subject: Node) -> str | None:
        for obj in graph.objects(subject, REGAL.license):
            if isinstance(obj, Literal):
                return str(obj)
            if isinstance(obj, URIRef):
                return str(obj)
            # Blank / non-URI nodes: prefer human-readable label over internal ids.
            pref = self._str(graph, obj, SKOS.prefLabel)
            if pref:
                return pref
        return None

    def _title(self, graph: Graph, subject: Node) -> str:
        title = self._str(graph, subject, DCTERMS.title)
        if title:
            return title
        pref = self._str(graph, subject, SKOS.prefLabel)
        return pref or "Untitled"

    def _doi(self, graph: Graph, subject: Node) -> str | None:
        doi = self._str(graph, subject, REGAL.doi)
        return doi.strip() if doi else None

    def _regal_id(self, subject: Node) -> str | None:
        if isinstance(subject, URIRef):
            value = str(subject)
            if value.startswith(self._resource_base_url):
                return value.removeprefix(self._resource_base_url)
            if value.startswith("frl:") or value.startswith("edoweb:"):
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
            slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", regal_id).strip("_")
            return slug or self._to_identifier_slug(title)
        if doi:
            return doi
        return self._to_identifier_slug(title)

    def _output_uri(self, *, regal_id: str | None, doi: str | None) -> str:
        if doi:
            return f"https://doi.org/{doi}"
        if regal_id:
            return self._resource_url(regal_id)
        return "unknown"

    def _resource_url(self, regal_id: str) -> str:
        return f"{self._resource_base_url}{quote(regal_id, safe=':')}"

    def _labelled_nodes(self, graph: Graph, subject: Node, predicate: Node) -> list[tuple[str, str | None]]:
        results: list[tuple[str, str | None]] = []
        for obj in graph.objects(subject, predicate):
            if isinstance(obj, Literal):
                results.append((str(obj), None))
                continue
            label = self._str(graph, obj, SKOS.prefLabel) or str(obj)
            results.append((label, str(obj)))
        return results

    def _str(self, graph: Graph, subject: Node, predicate: Node) -> str | None:
        value = graph.value(subject, predicate)
        return str(value) if value is not None else None

    def _strs(self, graph: Graph, subject: Node, predicate: Node) -> list[str]:
        return [str(obj) for obj in graph.objects(subject, predicate) if obj is not None]

    def _join_literals(self, graph: Graph, subject: Node, predicate: Node) -> str:
        return "\n\n".join(self._strs(graph, subject, predicate))

    @staticmethod
    def _split_pref_label(pref_label: str) -> tuple[str, str]:
        if ", " in pref_label:
            family, given = pref_label.split(", ", maxsplit=1)
            return family.strip(), given.strip()
        return pref_label.strip(), ""

    @staticmethod
    def _to_identifier_slug(title: str) -> str:
        if not title:
            return "untitled"
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        return slug[:80] or "untitled"
