"""Mapper module for converting Schema.org RDF graphs to ARC objects.

THIS IS AN EXAMPLE IMPLEMENTATION. A PRODUCTION-READY IMPLEMENTATION WOULD
REQUIRE A DEFINITIVE SPEC HOW TO MAP SCHEMA.ORG TO ARC IN A MEANINGFUL WAY.
GeneralSchemaOrgMapper works directly on rdflib.Graph throughout —
no intermediate model layer is created between the graph and the ARC output.
"""

import re
from typing import cast

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
from rdflib import Graph, Literal, Namespace  # type: ignore[import-untyped]
from rdflib.namespace import RDF
from rdflib.term import Node

from ..config import PayloadType
from .schema_org_mapper import SchemaOrgMapper


@SchemaOrgMapper.register(PayloadType.general)
class GeneralSchemaOrgMapper(SchemaOrgMapper):
    """Maps a Schema.org RDF graph to ARC objects.

    Works entirely on rdflib.Graph — no intermediate model layer is constructed.
    """

    SCHEMA_URIS = [
        Namespace("https://schema.org/"),
        Namespace("http://schema.org/"),
    ]

    def __init__(self) -> None:
        """Initialize mapper state for the active Schema.org namespace."""
        self._active_schema: Namespace | None = None

    def _schema(self) -> Namespace:
        return self._active_schema or self.SCHEMA_URIS[0]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map_graph(self, graph: Graph) -> str:
        """Map an RDF graph to a serialized RO-Crate JSON-LD string."""
        schema, subject = self._find_dataset_subject(graph)
        if subject is None:
            raise ValueError("Graph does not contain a Schema.org Dataset entity")

        self._active_schema = schema
        try:
            arc = self._map_arc(graph, subject)
        finally:
            self._active_schema = None

        return cast(str, arc.ToROCrateJsonString())

    # ------------------------------------------------------------------
    # Graph traversal helpers
    # ------------------------------------------------------------------

    def _find_dataset_subject(self, graph: Graph) -> tuple[Namespace, Node | None]:
        for schema in self.SCHEMA_URIS:
            subjects = list(graph.subjects(RDF.type, schema.Dataset))
            if subjects:
                return schema, subjects[0]
        return self.SCHEMA_URIS[0], next(iter(graph.subjects()), None)

    def _obj(self, graph: Graph, subject: Node, predicate: Node) -> Node | None:
        return graph.value(subject, predicate)

    def _str(self, graph: Graph, subject: Node, predicate: Node) -> str | None:
        value = self._obj(graph, subject, predicate)
        return str(value) if value is not None else None

    def _strs(self, graph: Graph, subject: Node, predicate: Node) -> list[str]:
        return [str(obj) for obj in graph.objects(subject, predicate) if obj is not None]

    def _is_type(self, graph: Graph, node: Node, rdf_type: Node) -> bool:
        return (node, RDF.type, rdf_type) in graph

    # ------------------------------------------------------------------
    # Identifier helpers
    # ------------------------------------------------------------------

    def _to_identifier_slug(self, title: str) -> str:
        if not title:
            return "untitled"
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        return slug[:80]

    def _extract_doi(self, graph: Graph, subject: Node) -> str | None:
        identifier = self._str(graph, subject, self._schema().identifier)
        if identifier and identifier.startswith("10."):
            return identifier
        subject_str = str(subject)
        doi_match = re.search(r"doi\.org/(?P<doi>10\.[^/?#]+)", subject_str, re.IGNORECASE)
        if doi_match:
            return doi_match.group("doi")
        if subject_str.startswith("10."):
            return subject_str
        return None

    # ------------------------------------------------------------------
    # ARC assembly
    # ------------------------------------------------------------------

    def _map_arc(self, graph: Graph, subject: Node) -> ARC:
        investigation = self._map_investigation(graph, subject)
        study = self._map_study(graph, subject)
        investigation.AddStudy(study)
        assay = self._map_assay(graph, subject)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)
        return ARC.from_arc_investigation(investigation)

    def _map_investigation(self, graph: Graph, subject: Node) -> ArcInvestigation:
        doi = self._extract_doi(graph, subject)
        title = self._str(graph, subject, self._schema().name) or "Untitled Dataset"
        identifier = doi or str(subject) or self._to_identifier_slug(title)
        if identifier and ("://" in identifier or "/" in identifier):
            identifier = self._to_identifier_slug(title) or identifier.split("/")[-1]

        description = self._str(graph, subject, self._schema().description) or ""
        submission_date = (
            self._str(graph, subject, self._schema().datePublished)
            or self._str(graph, subject, self._schema().dateModified)
            or ""
        )

        inv = ArcInvestigation.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=submission_date,
        )

        self._add_contacts(inv, graph, subject)
        self._add_publications(inv, graph, subject, doi)
        self._add_investigation_comments(inv, graph, subject)
        self._add_ontology_sources(inv)
        return inv

    def _add_ontology_sources(self, inv: ArcInvestigation) -> None:
        inv.OntologySourceReferences.append(
            OntologySourceReference.create(
                name="SCHEMAORG",
                file="https://schema.org/",
                version="",
                description="Schema.org vocabulary for structured data",
            )
        )
        for name, url, desc in [
            ("NCIT", "http://purl.obolibrary.org/obo/ncit.owl", "NCI Thesaurus"),
            ("EDAM", "http://edamontology.org", "EDAM Bioinformatics Ontology"),
        ]:
            inv.OntologySourceReferences.append(
                OntologySourceReference.create(name=name, file=url, version="", description=desc)
            )

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    def _add_contacts(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        for node in graph.objects(subject, self._schema().creator):
            self._append_contact(inv, graph, node, "author")
        for node in graph.objects(subject, self._schema().author):
            if not self._contact_exists(inv, graph, node):
                self._append_contact(inv, graph, node, "author")
        for node in graph.objects(subject, self._schema().contributor):
            self._append_contact(inv, graph, node, "contributor")
        publisher_node = self._obj(graph, subject, self._schema().publisher)
        if publisher_node is not None:
            self._append_contact(inv, graph, publisher_node, "publisher")

    def _append_contact(self, inv: ArcInvestigation, graph: Graph, node: Node, role: str) -> None:
        person = self._node_to_person(graph, node)
        if person is None:
            return
        person.Roles.append(OntologyAnnotation(name=role))
        inv.Contacts.append(person)

    def _contact_exists(self, inv: ArcInvestigation, graph: Graph, node: Node) -> bool:
        given = self._str(graph, node, self._schema().givenName) or ""
        family = self._str(graph, node, self._schema().familyName) or ""
        if not given and not family:
            name = self._str(graph, node, self._schema().name) or ""
            parts = name.split(" ")
            family = parts[-1] if parts else ""
            given = " ".join(parts[:-1]) if len(parts) > 1 else name
        return any(c.FirstName == given and c.LastName == family for c in inv.Contacts)

    def _node_to_person(self, graph: Graph, node: Node) -> Person | None:
        if isinstance(node, Literal):
            literal_name = str(node)
            return Person.create(last_name=literal_name, first_name="") if literal_name else None

        if self._is_type(graph, node, self._schema().Organization):
            org_name = self._str(graph, node, self._schema().name)
            return (
                Person.create(last_name=org_name or "", first_name="", affiliation=org_name or "") if org_name else None
            )

        given = self._str(graph, node, self._schema().givenName) or ""
        family = self._str(graph, node, self._schema().familyName) or ""
        name = self._str(graph, node, self._schema().name)
        email = self._str(graph, node, self._schema().email)
        url = self._str(graph, node, self._schema().url)

        if not given and not family and not name:
            return None

        if not given and not family and name:
            parts = name.split(" ")
            family = parts[-1] if parts else ""
            given = " ".join(parts[:-1]) if len(parts) > 1 else name

        address = self._extract_address(graph, node)
        arc_person = Person.create(last_name=family, first_name=given, email=email, address=address)
        if url:
            arc_person.Comments.append(Comment.create("URL", url))
        return arc_person

    def _extract_address(self, graph: Graph, node: Node) -> str | None:
        addr_node = self._obj(graph, node, self._schema().address)
        if addr_node is None:
            return None
        if isinstance(addr_node, Literal):
            return str(addr_node)
        parts = [
            self._str(graph, addr_node, self._schema().streetAddress),
            self._str(graph, addr_node, self._schema().postalCode),
            self._str(graph, addr_node, self._schema().addressCountry),
        ]
        return ", ".join(p for p in parts if p) or None

    # ------------------------------------------------------------------
    # Publications
    # ------------------------------------------------------------------

    def _add_publications(self, inv: ArcInvestigation, graph: Graph, subject: Node, doi: str | None) -> None:
        if doi:
            authors = [p for p in inv.Contacts if any(r.Name == "author" for r in p.Roles)]
            author_strs: list[str] = []
            for p in authors:
                if p.FirstName and p.LastName:
                    author_strs.append(f"{p.LastName}, {p.FirstName[0]}.")
                elif p.LastName:
                    author_strs.append(p.LastName)
                elif p.FirstName:
                    author_strs.append(p.FirstName)

            inv.Publications.append(
                Publication.create(
                    title=self._str(graph, subject, self._schema().name) or "Untitled",
                    authors="; ".join(author_strs) if author_strs else None,
                    doi=doi,
                )
            )

        for citation in self._strs(graph, subject, self._schema().citation):
            if citation and citation not in [p.DOI for p in inv.Publications]:
                inv.Publications.append(Publication.create(title=citation[:200], authors=None))

    # ------------------------------------------------------------------
    # Investigation comments
    # ------------------------------------------------------------------

    def _add_investigation_comments(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        keywords = self._strs(graph, subject, self._schema().keywords)
        if keywords:
            inv.Comments.append(Comment.create("Keywords", ", ".join(keywords)))

        for label, predicate in [
            ("License", self._schema().license),
            ("Language", self._schema().inLanguage),
            ("Version", self._schema().version),
            ("URL", self._schema().url),
        ]:
            value = self._str(graph, subject, predicate)
            if value:
                inv.Comments.append(Comment.create(label, value))

        conforms_to = self._obj(graph, subject, self._schema().conformsTo)
        if conforms_to is not None:
            inv.Comments.append(Comment.create("Conforms To", str(conforms_to)))

        for dist_node in graph.objects(subject, self._schema().distribution):
            if isinstance(dist_node, Literal):
                continue
            encoding = self._str(graph, dist_node, self._schema().encodingFormat) or ""
            content_url = self._str(graph, dist_node, self._schema().contentUrl) or ""
            if encoding or content_url:
                inv.Comments.append(Comment.create("Distribution", f"{encoding}: {content_url}"))

    # ------------------------------------------------------------------
    # Study
    # ------------------------------------------------------------------

    def _map_study(self, graph: Graph, subject: Node) -> ArcStudy:
        title = self._str(graph, subject, self._schema().name) or "Untitled Dataset"
        identifier = self._to_identifier_slug(title) or "dataset"
        description = self._str(graph, subject, self._schema().description) or "Imported from Schema.org metadata"

        study = ArcStudy.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=self._str(graph, subject, self._schema().datePublished),
        )

        collection_table = self._create_data_collection_table(graph, subject)
        if collection_table:
            study.AddTable(collection_table)
        study.AddTable(self._create_data_processing_table(graph, subject))
        return study

    def _create_data_collection_table(self, graph: Graph, subject: Node) -> ArcTable | None:
        keywords = self._strs(graph, subject, self._schema().keywords)
        description = self._str(graph, subject, self._schema().description)
        if not (keywords or description):
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

        note = "Data processing and publication according to Schema.org metadata standard"
        publisher_node = self._obj(graph, subject, self._schema().publisher)
        if publisher_node is not None:
            publisher_name = self._str(graph, publisher_node, self._schema().name)
            if publisher_name:
                note += f" | Publisher: {publisher_name}"

        table.AddColumn(
            CompositeHeader.parameter(OntologyAnnotation(name="Processing Description")),
            [CompositeCell.term(OntologyAnnotation(name=note))],
        )
        table.AddColumn(
            CompositeHeader.output(IOType.data()),
            [CompositeCell.create_data_from_string("Published Dataset")],
        )
        return table

    # ------------------------------------------------------------------
    # Assay
    # ------------------------------------------------------------------

    def _map_assay(self, graph: Graph, subject: Node) -> ArcAssay:
        title = self._str(graph, subject, self._schema().name) or "Untitled Dataset"
        identifier = self._to_identifier_slug(title) or "dataset"

        assay = ArcAssay.create(
            identifier=identifier,
            title=title,
            measurement_type=OntologyAnnotation(name="Data Collection"),
            technology_type=OntologyAnnotation(name="Data Repository"),
        )
        assay.TechnologyPlatform = OntologyAnnotation(name="Schema.org Data Repository")
        assay.AddTable(self._create_assay_table(graph, subject))
        return assay

    def _create_assay_table(self, graph: Graph, subject: Node) -> ArcTable:
        url = self._str(graph, subject, self._schema().url) or str(subject)

        table = ArcTable.init("Measurement")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Dataset Source")],
        )
        table.AddColumn(
            CompositeHeader.output(IOType.of_string("URI")),
            [CompositeCell.free_text(url)],
        )

        license_val = self._str(graph, subject, self._schema().license)
        if license_val:
            table.AddColumn(
                CompositeHeader.comment("License"),
                [CompositeCell.free_text(license_val)],
            )

        publisher_node = self._obj(graph, subject, self._schema().publisher)
        if publisher_node is not None:
            publisher_name = self._str(graph, publisher_node, self._schema().name) or "Unknown Publisher"
            table.AddColumn(
                CompositeHeader.comment("Publisher"),
                [CompositeCell.free_text(publisher_name)],
            )

        language = self._str(graph, subject, self._schema().inLanguage)
        if language:
            table.AddColumn(
                CompositeHeader.comment("Language"),
                [CompositeCell.free_text(language)],
            )

        return table
