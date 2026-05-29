"""Mapper module for converting e!DAL (IPK Gatersleben) Schema.org RDF graphs to ARC objects.

EDAL-specific quirks handled:
  - ORCID extraction from author @id / identifier PropertyValue
  - DC namespace (http://purl.org/dc/terms/conformsTo) for Bioschemas references
  - Non-ISO datePublished format (Java Date.toString())
  - Flat-string address on creator nodes
  - Bare DOI as @id (no https://doi.org/ prefix)
"""

import re

from arctrl import (  # type: ignore[import-untyped]
    ARC,
    ArcInvestigation,
    Comment,
    OntologyAnnotation,
    Person,
    Publication,
)
from arctrl.py.Core.ontology_source_reference import OntologySourceReference
from rdflib import Graph, Literal, Namespace, URIRef  # type: ignore[import-untyped]
from rdflib.namespace import RDF
from rdflib.term import Node

from ..config import PayloadType
from .schema_org_mapper import SchemaOrgMapper

_DC_CONFORMS_TO = URIRef("http://purl.org/dc/terms/conformsTo")


@SchemaOrgMapper.register(PayloadType.edal)
class EdalSchemaOrgMapper(SchemaOrgMapper):
    """Maps an e!DAL schema.org RDF graph to ARC Investigation.

    Investigation-focused: title, description, contacts (with ORCID),
    publications, and metadata comments (license, keywords, language,
    conformsTo). Does not create Study or Assay.
    """

    SCHEMA_URIS = [
        Namespace("https://schema.org/"),
        Namespace("http://schema.org/"),
    ]

    _ORCID_PATTERN = re.compile(r"orcid\.org/(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", re.IGNORECASE)

    def __init__(self) -> None:
        """Initialize mapper with no active schema namespace."""
        self._active_schema: Namespace | None = None

    def _schema(self) -> Namespace:
        return self._active_schema or self.SCHEMA_URIS[0]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map_graph(self, graph: Graph) -> str:
        """Map an rdflib Graph to serialized RO-Crate JSON-LD string."""
        schema, subject = self._find_dataset_subject(graph)
        if subject is None:
            raise ValueError("Graph does not contain a Schema.org Dataset entity")

        self._active_schema = schema
        try:
            arc = self._map_arc(graph, subject)
        finally:
            self._active_schema = None

        return str(arc.ToROCrateJsonString())

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
    # ARC assembly
    # ------------------------------------------------------------------

    def _map_arc(self, graph: Graph, subject: Node) -> ARC:
        investigation = self._map_investigation(graph, subject)
        return ARC.from_arc_investigation(investigation)

    def _map_investigation(self, graph: Graph, subject: Node) -> ArcInvestigation:
        title = self._str(graph, subject, self._schema().name) or "Untitled Dataset"
        description = self._str(graph, subject, self._schema().description) or "Imported from e!DAL repository"
        submission_date = (
            self._str(graph, subject, self._schema().datePublished)
            or self._str(graph, subject, self._schema().dateModified)
            or ""
        )

        identifier = self._extract_identifier(graph, subject)
        if not identifier:
            identifier = self._to_identifier_slug(title)

        inv = ArcInvestigation.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=submission_date,
        )

        self._add_contacts(inv, graph, subject)
        self._add_publications(inv, graph, subject)
        self._add_investigation_comments(inv, graph, subject)
        self._add_ontology_sources(inv)
        return inv

    def _extract_identifier(self, graph: Graph, subject: Node) -> str | None:
        schema = self._schema()
        identifier = self._str(graph, subject, schema.identifier)
        if identifier:
            return identifier
        subject_str = str(subject)
        if subject_str.startswith("10."):
            return subject_str
        doi_match = re.search(r"doi\.org/(10\.[^/?#]+)", subject_str, re.IGNORECASE)
        if doi_match:
            return doi_match.group(1)
        return None

    @staticmethod
    def _to_identifier_slug(title: str) -> str:
        if not title:
            return "untitled"
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        return slug[:80]

    @staticmethod
    def _add_ontology_sources(inv: ArcInvestigation) -> None:
        for name, url, desc in [
            ("SCHEMAORG", "https://schema.org/", "Schema.org vocabulary for structured data"),
            ("NCIT", "http://purl.obolibrary.org/obo/ncit.owl", "NCI Thesaurus"),
            ("EDAM", "http://edamontology.org", "EDAM Bioinformatics Ontology"),
        ]:
            inv.OntologySourceReferences.append(
                OntologySourceReference.create(name=name, file=url, version="", description=desc)
            )

    # ------------------------------------------------------------------
    # Contacts (authors, creators, publisher)
    # ------------------------------------------------------------------

    def _add_contacts(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        for node in graph.objects(subject, self._schema().creator):
            self._append_contact(inv, graph, node, "author")
        for node in graph.objects(subject, self._schema().author):
            if not self._contact_exists(inv, graph, node):
                self._append_contact(inv, graph, node, "author")
        publisher_node = self._obj(graph, subject, self._schema().publisher)
        if publisher_node is not None:
            self._append_contact(inv, graph, publisher_node, "publisher")

    def _append_contact(self, inv: ArcInvestigation, graph: Graph, node: Node, role: str) -> None:
        person = self._node_to_person(graph, node)
        if person is None:
            return
        person.Roles.append(OntologyAnnotation(name=role))
        self._add_orcid_comment(graph, node, person)
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

        if not given and not family and not name:
            return None

        if not given and not family and name:
            parts = name.split(" ")
            family = parts[-1] if parts else ""
            given = " ".join(parts[:-1]) if len(parts) > 1 else name

        address = self._extract_address(graph, node)
        return Person.create(last_name=family, first_name=given, email=email, address=address)

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

    def _add_orcid_comment(self, graph: Graph, node: Node, person: Person) -> None:
        orcid = self._extract_orcid(graph, node)
        if orcid:
            person.Comments.append(Comment.create("ORCID", orcid))

    def _extract_orcid(self, graph: Graph, node: Node) -> str | None:
        node_id = self._str(graph, node, self._schema().identifier)
        if node_id:
            match = self._ORCID_PATTERN.search(node_id)
            if match:
                return match.group(1)
            if node_id.startswith("0000-") or re.match(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", node_id):
                return node_id

        node_uri = str(node)
        match = self._ORCID_PATTERN.search(node_uri)
        if match:
            return match.group(1)

        identifier_node = self._obj(graph, node, self._schema().identifier)
        if identifier_node and not isinstance(identifier_node, Literal):
            value = self._str(graph, identifier_node, self._schema().value)
            if value and re.match(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", value):
                return value

        return None

    # ------------------------------------------------------------------
    # Publications
    # ------------------------------------------------------------------

    def _add_publications(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        doi = self._extract_identifier(graph, subject)
        if not doi:
            return

        authors = [p for p in inv.Contacts if any(r.Name == "author" for r in p.Roles)]
        author_strs: list[str] = []
        for p in authors:
            if p.FirstName and p.LastName:
                author_strs.append(f"{p.LastName}, {p.FirstName[0]}.")
            elif p.LastName:
                author_strs.append(p.LastName)

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

        self._add_conforms_to_comment(inv, graph, subject)

        for dist_node in graph.objects(subject, self._schema().distribution):
            if isinstance(dist_node, Literal):
                continue
            encoding = self._str(graph, dist_node, self._schema().encodingFormat) or ""
            content_url = self._str(graph, dist_node, self._schema().contentUrl) or ""
            if encoding or content_url:
                inv.Comments.append(Comment.create("Distribution", f"{encoding}: {content_url}"))

    def _add_conforms_to_comment(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        conforms_node = self._obj(graph, subject, _DC_CONFORMS_TO)
        if conforms_node is None:
            conforms_node = self._obj(graph, subject, self._schema().conformsTo)
        if conforms_node is not None:
            conforms_id = self._str(graph, conforms_node, Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#").id)
            if not conforms_id:
                conforms_id = str(conforms_node)
            inv.Comments.append(Comment.create("Conforms To", conforms_id))
