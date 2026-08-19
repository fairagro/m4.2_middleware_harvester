"""Mapper module for converting Schema.org RDF graphs to ARC objects.

THIS IS AN EXAMPLE IMPLEMENTATION. A PRODUCTION-READY IMPLEMENTATION WOULD
REQUIRE A DEFINITIVE SPEC HOW TO MAP SCHEMA.ORG TO ARC IN A MEANINGFUL WAY.
GeneralSchemaOrgMapper works directly on rdflib.Graph throughout —
no intermediate model layer is created between the graph and the ARC output.
"""

import re

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
from rdflib import Graph, Literal, Namespace, URIRef  # type: ignore[import-untyped]
from rdflib.namespace import RDF
from rdflib.term import BNode, Node

from middleware.harvester.plugin_base import HarvestedArc

from ..config import PayloadType
from .linked_data_mapper import LinkedDataMapper
from .person_contacts import require_nonempty_person_given_names


@LinkedDataMapper.register(PayloadType.schema_org_general)
class GeneralSchemaOrgMapper(LinkedDataMapper):
    """Maps a Schema.org RDF graph to ARC objects.

    Works entirely on rdflib.Graph — no intermediate model layer is constructed.
    """

    SCHEMA_URIS = [
        Namespace("https://schema.org/"),
        Namespace("http://schema.org/"),
    ]

    _DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", re.IGNORECASE)
    _RECEIVE_ID_RE = re.compile(r"/receive/([^/?#]+)", re.IGNORECASE)

    def __init__(self) -> None:
        """Initialize mapper state for the active Schema.org namespace."""
        self._active_schema: Namespace | None = None

    def _schema(self) -> Namespace:
        return self._active_schema or self.SCHEMA_URIS[0]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map_graph(self, graph: Graph, source_url: str | None = None) -> HarvestedArc:
        """Map an RDF graph to a harvested ARC with composition counts."""
        schema, subject = self._find_dataset_subject(graph)
        if subject is None:
            raise ValueError("Graph does not contain a Schema.org Dataset entity")

        self._active_schema = schema
        try:
            arc = self._map_arc(graph, subject, source_url=source_url)
        finally:
            self._active_schema = None

        return HarvestedArc.from_arctrl(arc)

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

    def _schema_objects(self, graph: Graph, subject: Node, term: str) -> list[Node]:
        """Return objects for a Schema.org term under both http and https namespaces."""
        seen: set[Node] = set()
        objects: list[Node] = []
        for schema in self.SCHEMA_URIS:
            for obj in graph.objects(subject, getattr(schema, term)):
                if obj not in seen:
                    seen.add(obj)
                    objects.append(obj)
        return objects

    def _normalize_doi(self, raw: str) -> str | None:
        text = self._DOI_PREFIX_RE.sub("", raw.strip()).strip()
        if text.startswith("10.") and "/" in text:
            return text
        return None

    def _doi_from_identifier_node(self, graph: Graph, node: Node) -> str | None:
        if isinstance(node, Literal):
            return self._normalize_doi(str(node))
        if isinstance(node, URIRef):
            return self._normalize_doi(str(node))
        return self._doi_from_property_value(graph, node)

    def _doi_from_property_value(self, graph: Graph, node: Node) -> str | None:
        property_ids = [str(obj) for obj in self._schema_objects(graph, node, "propertyID") if obj is not None]
        values = [str(obj) for obj in self._schema_objects(graph, node, "value") if obj is not None]
        if not values:
            return None
        if not property_ids or not any("doi" in pid.lower() for pid in property_ids):
            return None
        for value in values:
            doi = self._normalize_doi(value)
            if doi:
                return doi
        return None

    def _extract_doi(self, graph: Graph, subject: Node) -> str | None:
        for obj in self._schema_objects(graph, subject, "identifier"):
            doi = self._doi_from_identifier_node(graph, obj)
            if doi:
                return doi
        if isinstance(subject, URIRef):
            return self._normalize_doi(str(subject))
        return None

    def _http_iri(self, node: Node) -> str | None:
        if isinstance(node, BNode):
            return None
        if isinstance(node, (Literal, URIRef)):
            text = str(node).strip()
            if text.startswith(("http://", "https://")):
                return text
        return None

    def _catalog_identifier_from_url(self, url: str) -> str:
        match = self._RECEIVE_ID_RE.search(url)
        if match:
            return match.group(1)
        return url

    def _first_http_identifier(self, graph: Graph, subject: Node, term: str) -> str | None:
        for obj in self._schema_objects(graph, subject, term):
            iri = self._http_iri(obj)
            if iri:
                return self._catalog_identifier_from_url(iri)
        return None

    def _resolve_investigation_identifier(
        self, graph: Graph, subject: Node, source_url: str | None, doi: str | None
    ) -> str:
        if doi:
            return doi

        for term in ("url", "sameAs"):
            identifier = self._first_http_identifier(graph, subject, term)
            if identifier:
                return identifier

        subject_iri = self._http_iri(subject)
        if subject_iri:
            return self._catalog_identifier_from_url(subject_iri)

        if source_url:
            text = source_url.strip()
            if text.startswith(("http://", "https://")):
                return self._catalog_identifier_from_url(text)

        raise ValueError(
            "Schema.org Dataset has no stable identifier "
            "(DOI, http(s) URL, or MyCoRe catalog id); refusing blank-node identifier"
        )

    # ------------------------------------------------------------------
    # ARC assembly
    # ------------------------------------------------------------------

    def _map_arc(self, graph: Graph, subject: Node, source_url: str | None = None) -> ARC:
        investigation = self._map_investigation(graph, subject, source_url=source_url)
        study = self._map_study(graph, subject)
        investigation.AddStudy(study)
        assay = self._map_assay(graph, subject, source_url=source_url)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)
        return ARC.from_arc_investigation(investigation)

    def _map_investigation(self, graph: Graph, subject: Node, source_url: str | None = None) -> ArcInvestigation:
        doi = self._extract_doi(graph, subject)
        title = self._str(graph, subject, self._schema().name) or "Untitled Dataset"
        identifier = self._resolve_investigation_identifier(graph, subject, source_url, doi)

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
        # Organization publishers are Investigation comments, not Person contacts.
        require_nonempty_person_given_names(inv)

    def _append_contact(self, inv: ArcInvestigation, graph: Graph, node: Node, role: str) -> None:
        if not isinstance(node, Literal) and self._is_type(graph, node, self._schema().Organization):
            self._append_organization_comment(inv, graph, node, role)
            return
        person = self._node_to_person(graph, node)
        if person is None:
            return
        person.Roles.append(OntologyAnnotation(name=role))
        inv.Contacts.append(person)

    def _append_organization_comment(self, inv: ArcInvestigation, graph: Graph, node: Node, role: str) -> None:
        org_name = self._str(graph, node, self._schema().name)
        if not org_name:
            return
        comment_name = "Publisher" if role == "publisher" else role.capitalize()
        inv.Comments.append(Comment.create(comment_name, org_name))
        org_url = self._str(graph, node, self._schema().url) or (
            str(node) if not isinstance(node, Literal) and str(node).startswith("http") else None
        )
        if org_url:
            inv.Comments.append(Comment.create(f"{comment_name} URL", org_url))

    def _contact_exists(self, inv: ArcInvestigation, graph: Graph, node: Node) -> bool:
        given, family = self._person_names(graph, node)
        if given is None:
            return False
        return any(c.FirstName == given and c.LastName == family for c in inv.Contacts)

    def _person_names(self, graph: Graph, node: Node) -> tuple[str | None, str]:
        """Return ``(given, family)`` or ``(None, ...)`` when given name would be empty."""
        if isinstance(node, Literal):
            return self._split_display_name(str(node))

        if self._is_type(graph, node, self._schema().Organization):
            return None, self._str(graph, node, self._schema().name) or ""

        given = (self._str(graph, node, self._schema().givenName) or "").strip()
        family = (self._str(graph, node, self._schema().familyName) or "").strip()
        name = self._str(graph, node, self._schema().name)

        # Common Schema.org shape: familyName set, givenName missing, full display in name.
        if not given and name:
            given_opt, family_from_name = self._split_display_name(name)
            if given_opt:
                given = given_opt
            if not family:
                family = family_from_name

        if not given:
            return None, family
        return given, family

    @staticmethod
    def _split_display_name(name: str) -> tuple[str | None, str]:
        parts = name.strip().split()
        if not parts:
            return None, ""
        if len(parts) == 1:
            return None, parts[0]
        return " ".join(parts[:-1]), parts[-1]

    def _node_to_person(self, graph: Graph, node: Node) -> Person | None:
        if isinstance(node, Literal):
            given, family = self._split_display_name(str(node))
            if given is None:
                if family:
                    raise ValueError(f"Person contact must have a non-empty given name (last_name={family!r})")
                return None
            return Person.create(last_name=family, first_name=given)

        if self._is_type(graph, node, self._schema().Organization):
            return None

        given, family = self._person_names(graph, node)
        email = self._str(graph, node, self._schema().email)
        url = self._str(graph, node, self._schema().url)

        if given is None:
            if family or self._str(graph, node, self._schema().name):
                raise ValueError(f"Person contact must have a non-empty given name (last_name={family!r})")
            return None

        affiliation = self._extract_affiliation(graph, node)
        address = self._extract_address(graph, node)
        arc_person = Person.create(
            last_name=family,
            first_name=given,
            email=email,
            address=address,
            affiliation=affiliation or "",
        )
        if url:
            arc_person.Comments.append(Comment.create("URL", url))
        return arc_person

    def _extract_affiliation(self, graph: Graph, node: Node) -> str | None:
        aff_node = self._obj(graph, node, self._schema().affiliation)
        if aff_node is None:
            return None
        if isinstance(aff_node, Literal):
            return str(aff_node).strip() or None
        return self._str(graph, aff_node, self._schema().name)

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

        self._add_publisher_comment(inv, graph, subject)

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

    def _add_publisher_comment(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        publisher_node = self._obj(graph, subject, self._schema().publisher)
        if publisher_node is None:
            return
        if isinstance(publisher_node, Literal):
            inv.Comments.append(Comment.create("Publisher", str(publisher_node)))
            return
        if self._is_type(graph, publisher_node, self._schema().Organization):
            self._append_organization_comment(inv, graph, publisher_node, "publisher")
            return
        pub_name = self._str(graph, publisher_node, self._schema().name) or str(publisher_node)
        if pub_name:
            inv.Comments.append(Comment.create("Publisher", pub_name))

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

    def _map_assay(self, graph: Graph, subject: Node, source_url: str | None = None) -> ArcAssay:
        title = self._str(graph, subject, self._schema().name) or "Untitled Dataset"
        identifier = self._to_identifier_slug(title) or "dataset"

        assay = ArcAssay.create(
            identifier=identifier,
            title=title,
            measurement_type=OntologyAnnotation(name="Data Collection"),
            technology_type=OntologyAnnotation(name="Data Repository"),
        )
        assay.TechnologyPlatform = OntologyAnnotation(name="Schema.org Data Repository")
        assay.AddTable(self._create_assay_table(graph, subject, source_url=source_url))
        return assay

    def _create_assay_table(self, graph: Graph, subject: Node, source_url: str | None = None) -> ArcTable:
        url: str | None = None
        for obj in self._schema_objects(graph, subject, "url"):
            url = self._http_iri(obj)
            if url:
                break
        # Prefer canonical URL properties when present; otherwise fall back to
        # subject/sameAs if the dataset subject is a real HTTP(S) IRI.
        if url is None:
            url = self._first_http_identifier(graph, subject, "sameAs")
        if url is None:
            url = self._http_iri(subject)
        if url is None and source_url and source_url.startswith(("http://", "https://")):
            url = source_url
        url = url or ""

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
