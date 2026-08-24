"""Mapper module for converting Schema.org RDF graphs to ARC objects.

THIS IS AN EXAMPLE IMPLEMENTATION. A PRODUCTION-READY IMPLEMENTATION WOULD
REQUIRE A DEFINITIVE SPEC HOW TO MAP SCHEMA.ORG TO ARC IN A MEANINGFUL WAY.
GeneralSchemaOrgMapper works directly on rdflib.Graph throughout —
no intermediate model layer is created between the graph and the ARC output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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


@dataclass(frozen=True)
class _IdentifierPlan:
    """Resolved investigation identifier and DOI metadata for one Dataset."""

    investigation_id: str
    publication_doi: str | None
    alternate_dois: tuple[str, ...]


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
    _FORBIDDEN_ID_CHARS = re.compile(r"[^a-zA-Z0-9 _-]")
    # Bound nested BNode walks in sort keys (cycle-safe; never uses BNode labels).
    _STABLE_BNODE_MAX_DEPTH = 2

    def __init__(self) -> None:
        """Initialize mapper state for the active Schema.org namespace."""
        self._active_schema: Namespace | None = None

    def _schema(self) -> Namespace:
        return self._active_schema or self.SCHEMA_URIS[0]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map_graph(
        self,
        graph: Graph,
        source_url: str | None = None,
        *,
        harvest_source_id: str | None = None,
    ) -> HarvestedArc:
        """Map an RDF graph to a harvested ARC with composition counts."""
        schema, subject = self._find_dataset_subject(graph)
        if subject is None:
            raise ValueError("Graph does not contain a Schema.org Dataset entity")

        self._active_schema = schema
        try:
            arc = self._map_arc(graph, subject, source_url=source_url, harvest_source_id=harvest_source_id)
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
        """Return one object for ``predicate`` with deterministic multi-value selection.

        Prefer a non-empty Literal chosen by language policy (``en`` > ``de`` >
        untagged > other; longer then lexicographic ``casefold`` ties). If no
        Literal qualifies, prefer URIRefs over blank nodes, ranking blank nodes
        by a content signature (not the parser-local BNode label).
        """
        objects = list(graph.objects(subject, predicate))
        if not objects:
            return None
        chosen_literal = self._choose_literal([obj for obj in objects if isinstance(obj, Literal)])
        if chosen_literal is not None:
            return chosen_literal
        non_literals = [obj for obj in objects if not isinstance(obj, Literal)]
        if not non_literals:
            return None
        return sorted(non_literals, key=lambda node: self._stable_node_sort_key(graph, node))[0]

    def _stable_node_sort_key(
        self,
        graph: Graph,
        node: Node,
        *,
        _depth: int = 0,
        _visiting: frozenset[Node] | None = None,
    ) -> tuple[int, str]:
        """Deterministic sort key for URIRef / BNode / other non-Literals.

        Blank-node labels from rdflib are parser-local and MUST NOT be used for
        ranking. Nested blank nodes contribute a bounded content signature so
        BNode→BNode-only structures do not all collapse to ``""``. Predicates
        and literal objects are normalized without BNode labels and with
        language/datatype for uniqueness.
        """
        if isinstance(node, URIRef):
            return (0, str(node))
        if isinstance(node, BNode):
            visiting = _visiting or frozenset()
            if node in visiting or _depth > self._STABLE_BNODE_MAX_DEPTH:
                return (1, "")
            next_visiting = visiting | {node}
            parts: list[str] = []
            for predicate, obj in graph.predicate_objects(node):
                pred_token = self._stable_term_token(predicate)
                if pred_token is None:
                    continue
                if isinstance(obj, BNode):
                    nested_sig = self._stable_node_sort_key(
                        graph,
                        obj,
                        _depth=_depth + 1,
                        _visiting=next_visiting,
                    )[1]
                    parts.append(f"{pred_token}->[{nested_sig}]")
                else:
                    obj_token = self._stable_term_token(obj)
                    if obj_token is not None:
                        parts.append(f"{pred_token}={obj_token}")
            return (1, "|".join(sorted(parts)))
        return (2, str(node))

    @staticmethod
    def _stable_term_token(term: Node) -> str | None:
        """Serialize a term for signatures without parser-local BNode labels."""
        if isinstance(term, BNode):
            return None
        if isinstance(term, URIRef):
            text = str(term).strip()
            return text or None
        if isinstance(term, Literal):
            text = str(term).strip()
            if not text:
                return None
            lang = (term.language or "").casefold()
            datatype = str(term.datatype) if term.datatype is not None else ""
            return f"{text}|lang={lang}|dt={datatype}"
        text = str(term).strip()
        return text or None

    def _str(self, graph: Graph, subject: Node, predicate: Node) -> str | None:
        """Return ``str`` of :meth:`_obj`, stripped when the chosen node is a Literal."""
        value = self._obj(graph, subject, predicate)
        if value is None:
            return None
        text = str(value)
        return text.strip() if isinstance(value, Literal) else text

    def _strs(self, graph: Graph, subject: Node, predicate: Node) -> list[str]:
        """Return trimmed strings for ``predicate``, deduped and stably sorted.

        Literals and URIRefs are stringified directly. Blank nodes contribute
        ``schema:name`` when present and are skipped when unlabelled — never
        persist parser-local BNode labels. Dedup key is ``casefold``; among
        casing variants the lexicographically smallest original spelling is
        kept. Sort key is ``(casefold, original)``.
        """
        by_fold: dict[str, str] = {}
        for obj in graph.objects(subject, predicate):
            if obj is None:
                continue
            text = self._stable_object_text(graph, obj)
            if not text:
                continue
            fold = text.casefold()
            previous = by_fold.get(fold)
            if previous is None or text < previous:
                by_fold[fold] = text
        return sorted(by_fold.values(), key=lambda value: (value.casefold(), value))

    def _stable_object_text(self, graph: Graph, obj: Node) -> str | None:
        """Stable display text for a graph object; never return a BNode label."""
        if isinstance(obj, Literal):
            text = str(obj).strip()
            return text or None
        if isinstance(obj, URIRef):
            text = str(obj).strip()
            return text or None
        if isinstance(obj, BNode):
            name_node = self._obj(graph, obj, self._schema().name)
            if isinstance(name_node, Literal):
                text = str(name_node).strip()
                return text or None
            if isinstance(name_node, URIRef):
                text = str(name_node).strip()
                return text or None
            return None
        return None

    @staticmethod
    def _lang_rank(literal: Literal) -> int:
        lang = (literal.language or "").casefold()
        if lang == "en" or lang.startswith("en-"):
            return 0
        if lang == "de" or lang.startswith("de-"):
            return 1
        if lang == "":
            return 2
        return 3

    @classmethod
    def _choose_literal(cls, literals: list[Literal]) -> Literal | None:
        """Pick one Literal using only primitive, comparable key fields.

        Policy: non-empty; language rank ``en`` > ``de`` > untagged > other; then
        longer text; then lexicographic ``casefold`` / original text; then language
        tag and datatype strings. Never compares ``Literal`` objects directly.
        """
        best: Literal | None = None
        best_key: tuple[int, int, str, str, str, str] | None = None
        for literal in literals:
            text = str(literal).strip()
            if not text:
                continue
            lang = (literal.language or "").casefold()
            datatype = str(literal.datatype) if literal.datatype is not None else ""
            key = (
                cls._lang_rank(literal),
                -len(text),
                text.casefold(),
                text,
                lang,
                datatype,
            )
            if best_key is None or key < best_key:
                best_key = key
                best = literal
        return best

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
            doi = self._normalize_doi(str(node))
            if doi:
                return doi
            # URIRef may be the @id of a PropertyValue node; check nested fields.
            return self._doi_from_property_value(graph, node)
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

    def _extract_all_dois(self, graph: Graph, subject: Node) -> list[str]:
        """Collect every valid DOI from ``schema:identifier`` (deduped, sorted)."""
        by_fold: dict[str, str] = {}
        for obj in self._schema_objects(graph, subject, "identifier"):
            doi = self._doi_from_identifier_node(graph, obj)
            if not doi:
                continue
            fold = doi.casefold()
            previous = by_fold.get(fold)
            if previous is None or doi < previous:
                by_fold[fold] = doi
        if isinstance(subject, URIRef):
            subject_doi = self._normalize_doi(str(subject))
            if subject_doi:
                fold = subject_doi.casefold()
                previous = by_fold.get(fold)
                if previous is None or subject_doi < previous:
                    by_fold[fold] = subject_doi
        return sorted(by_fold.values(), key=str.casefold)

    @staticmethod
    def _pick_canonical_doi(dois: list[str]) -> str | None:
        if not dois:
            return None
        return min(dois, key=str.casefold)

    def _resolve_harvest_source_identifier(
        self,
        source_url: str | None,
        harvest_source_id: str | None = None,
    ) -> str | None:
        """Stable harvest-unit identifier from discovery (catalog id or page URL)."""
        if harvest_source_id and harvest_source_id.strip():
            return harvest_source_id.strip()
        if source_url:
            text = source_url.strip()
            if text.startswith(("http://", "https://")):
                return self._sanitize_identifier(text)
        return None

    def _resolve_graph_url_identifier(self, graph: Graph, subject: Node) -> str | None:
        for term in ("url", "sameAs"):
            identifier = self._canonical_http_identifier(graph, subject, term)
            if identifier:
                return self._sanitize_identifier(identifier)

        subject_iri = self._http_iri(subject)
        if subject_iri:
            return self._sanitize_identifier(subject_iri)
        return None

    def _extract_doi(self, graph: Graph, subject: Node) -> str | None:
        return self._pick_canonical_doi(self._extract_all_dois(graph, subject))

    def _http_iri(self, node: Node) -> str | None:
        if isinstance(node, BNode):
            return None
        if isinstance(node, (Literal, URIRef)):
            text = str(node).strip()
            if text.startswith(("http://", "https://")):
                return text
        return None

    def _canonical_http_identifier(self, graph: Graph, subject: Node, term: str) -> str | None:
        iris = [iri for obj in self._schema_objects(graph, subject, term) if (iri := self._http_iri(obj))]
        if not iris:
            return None
        return min(iris, key=str.casefold)

    @classmethod
    def _sanitize_identifier(cls, raw: str) -> str:
        """Make *raw* safe for arctrl ``Investigation.identifier``.

        Allowed characters: letters, digits, underscore, dash, space.
        Everything else (scheme separators ``://``, slashes, dots, …) is
        replaced with ``_``, then consecutive underscores are collapsed.
        """
        stripped = re.sub(r"^https?://", "", raw)
        sanitized = cls._FORBIDDEN_ID_CHARS.sub("_", stripped)
        sanitized = re.sub(r"_{2,}", "_", sanitized).strip("_")
        return sanitized

    def _identifier_plan_from_dois(self, all_dois: list[str]) -> tuple[str | None, tuple[str, ...]]:
        canonical_doi = self._pick_canonical_doi(all_dois)
        if not canonical_doi:
            return None, ()
        return canonical_doi, tuple(doi for doi in all_dois if doi != canonical_doi)

    def _plan_investigation_identifier(
        self,
        graph: Graph,
        subject: Node,
        source_url: str | None,
        harvest_source_id: str | None = None,
    ) -> _IdentifierPlan:
        all_dois = self._extract_all_dois(graph, subject)
        publication_doi, alternate_dois = self._identifier_plan_from_dois(all_dois)

        harvest_id = self._resolve_harvest_source_identifier(source_url, harvest_source_id)
        if harvest_id:
            return _IdentifierPlan(
                investigation_id=harvest_id,
                publication_doi=publication_doi,
                alternate_dois=alternate_dois,
            )

        graph_id = self._resolve_graph_url_identifier(graph, subject)
        if graph_id:
            return _IdentifierPlan(
                investigation_id=graph_id,
                publication_doi=publication_doi,
                alternate_dois=alternate_dois,
            )

        if publication_doi:
            return _IdentifierPlan(
                investigation_id=publication_doi,
                publication_doi=publication_doi,
                alternate_dois=alternate_dois,
            )

        raise ValueError(
            "Schema.org Dataset has no stable identifier "
            "(DOI, http(s) URL, or source URL); refusing blank-node identifier"
        )

    # ------------------------------------------------------------------
    # ARC assembly
    # ------------------------------------------------------------------

    def _map_arc(
        self,
        graph: Graph,
        subject: Node,
        source_url: str | None = None,
        harvest_source_id: str | None = None,
    ) -> ARC:
        identifier_plan = self._plan_investigation_identifier(
            graph,
            subject,
            source_url,
            harvest_source_id,
        )
        publication_doi = identifier_plan.publication_doi

        investigation = self._map_investigation(
            graph,
            subject,
            identifier_plan=identifier_plan,
        )
        study = self._map_study(graph, subject)
        investigation.AddStudy(study)
        assay = self._map_assay(graph, subject, source_url=source_url, doi=publication_doi)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)
        return ARC.from_arc_investigation(investigation)

    def _map_investigation(
        self,
        graph: Graph,
        subject: Node,
        *,
        identifier_plan: _IdentifierPlan,
    ) -> ArcInvestigation:
        plan = identifier_plan
        title = self._str(graph, subject, self._schema().name) or "Untitled Dataset"
        identifier = plan.investigation_id

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
        self._add_publications(inv, graph, subject, plan.publication_doi)
        self._add_alternate_identifier_comments(inv, plan.alternate_dois)
        self._add_investigation_comments(inv, graph, subject)
        self._add_ontology_sources(inv)
        return inv

    @staticmethod
    def _add_alternate_identifier_comments(inv: ArcInvestigation, alternate_dois: tuple[str, ...]) -> None:
        for doi in alternate_dois:
            inv.Comments.append(Comment.create("Alternate Identifier", doi))

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
        creators = sorted(
            graph.objects(subject, self._schema().creator),
            key=lambda node: self._contact_sort_key(graph, node),
        )
        for node in creators:
            self._append_contact(inv, graph, node, "author")

        authors = sorted(
            graph.objects(subject, self._schema().author),
            key=lambda node: self._contact_sort_key(graph, node),
        )
        for node in authors:
            if not self._contact_exists(inv, graph, node):
                self._append_contact(inv, graph, node, "author")

        contributors = sorted(
            graph.objects(subject, self._schema().contributor),
            key=lambda node: self._contact_sort_key(graph, node),
        )
        for node in contributors:
            self._append_contact(inv, graph, node, "contributor")
        # Organization publishers are Investigation comments, not Person contacts.
        require_nonempty_person_given_names(inv)

    def _contact_sort_key(self, graph: Graph, node: Node) -> tuple[str, str, str, tuple[int, str]]:
        """Stable sort key: family, given, display name, then node identity without BNode labels."""
        given, family = self._person_names(graph, node)
        if isinstance(node, Literal):
            display = str(node).strip()
        else:
            display = (self._str(graph, node, self._schema().name) or "").strip()
        return (
            (family or "").casefold(),
            (given or "").casefold(),
            display.casefold(),
            self._stable_node_sort_key(graph, node),
        )

    def _append_contact(self, inv: ArcInvestigation, graph: Graph, node: Node, role: str) -> None:
        if not isinstance(node, Literal) and self._is_type(graph, node, self._schema().Organization):
            self._append_organization_comment(inv, graph, node, role)
            return
        person = self._node_to_person(graph, node)
        if person is None:
            return
        person.Roles.append(OntologyAnnotation(name=role))
        inv.Contacts.append(person)

    def _append_organization_comment(self, inv: ArcInvestigation, graph: Graph, node: Node, role: str) -> bool:
        """Append Organization comment(s). Return True if a comment was emitted."""
        org_name = self._str(graph, node, self._schema().name)
        if not org_name:
            if isinstance(node, URIRef):
                org_name = str(node)
            else:
                return False
        comment_name = "Publisher" if role == "publisher" else role.capitalize()
        inv.Comments.append(Comment.create(comment_name, org_name))
        org_url = self._str(graph, node, self._schema().url) or (str(node) if isinstance(node, URIRef) else None)
        if org_url and org_url != org_name:
            inv.Comments.append(Comment.create(f"{comment_name} URL", org_url))
        return True

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
                    # Avoid "Last, F." — ARCtrl splits on commas into broken Author nodes.
                    author_strs.append(f"{p.FirstName[0]}. {p.LastName}")
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
        conforms_text = self._stable_object_text(graph, conforms_to) if conforms_to is not None else None
        if conforms_text:
            inv.Comments.append(Comment.create("Conforms To", conforms_text))

        for dist_node in graph.objects(subject, self._schema().distribution):
            if isinstance(dist_node, Literal):
                continue
            encoding = self._str(graph, dist_node, self._schema().encodingFormat) or ""
            content_url = self._str(graph, dist_node, self._schema().contentUrl) or ""
            if encoding or content_url:
                inv.Comments.append(Comment.create("Distribution", f"{encoding}: {content_url}"))

    def _add_publisher_comment(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        objects = list(graph.objects(subject, self._schema().publisher))
        if not objects:
            return
        # Prefer Organization / named resources over bare string literals when both exist.
        non_literals = sorted(
            (obj for obj in objects if not isinstance(obj, Literal)),
            key=lambda node: self._stable_node_sort_key(graph, node),
        )
        for publisher_node in non_literals:
            if self._is_type(graph, publisher_node, self._schema().Organization):
                if self._append_organization_comment(inv, graph, publisher_node, "publisher"):
                    return
                continue
            pub_name = self._str(graph, publisher_node, self._schema().name)
            if pub_name:
                inv.Comments.append(Comment.create("Publisher", pub_name))
                return
            if isinstance(publisher_node, URIRef):
                inv.Comments.append(Comment.create("Publisher", str(publisher_node)))
                return
        chosen_literal = self._choose_literal([obj for obj in objects if isinstance(obj, Literal)])
        if chosen_literal is not None:
            text = str(chosen_literal).strip()
            if text:
                inv.Comments.append(Comment.create("Publisher", text))

    def _resolve_publisher_label(self, graph: Graph, subject: Node) -> str | None:
        """Stable publisher display label for protocol/assay notes.

        Prefers a named Organization/resource (or URIRef IRI) over string
        literals when both are present — unlike :meth:`_obj`, which prefers
        Literals and would leave ``schema:name`` lookups empty.
        """
        objects = list(graph.objects(subject, self._schema().publisher))
        if not objects:
            return None
        non_literals = sorted(
            (obj for obj in objects if not isinstance(obj, Literal)),
            key=lambda node: self._stable_node_sort_key(graph, node),
        )
        for node in non_literals:
            name = self._str(graph, node, self._schema().name)
            if name:
                return name
            if isinstance(node, URIRef):
                return str(node)
        chosen_literal = self._choose_literal([obj for obj in objects if isinstance(obj, Literal)])
        if chosen_literal is None:
            return None
        text = str(chosen_literal).strip()
        return text or None

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
        publisher_name = self._resolve_publisher_label(graph, subject)
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

    def _map_assay(
        self, graph: Graph, subject: Node, source_url: str | None = None, doi: str | None = None
    ) -> ArcAssay:
        title = self._str(graph, subject, self._schema().name) or "Untitled Dataset"
        identifier = self._to_identifier_slug(title) or "dataset"

        assay = ArcAssay.create(
            identifier=identifier,
            title=title,
            measurement_type=OntologyAnnotation(name="Data Collection"),
            technology_type=OntologyAnnotation(name="Data Repository"),
        )
        assay.TechnologyPlatform = OntologyAnnotation(name="Schema.org Data Repository")
        assay.AddTable(self._create_assay_table(graph, subject, source_url=source_url, doi=doi))
        return assay

    def _resolve_assay_url(self, graph: Graph, subject: Node, source_url: str | None, doi: str | None) -> str:
        """Resolve the landing-page URL for the Measurement output URI cell.

        Unlike ``Investigation.identifier`` resolution, this keeps full URLs
        without compacting Receive-URL ``/receive/{id}`` paths to catalog ids.
        """
        for term in ("url", "sameAs"):
            for obj in self._schema_objects(graph, subject, term):
                iri = self._http_iri(obj)
                if iri:
                    return iri

        subject_iri = self._http_iri(subject)
        if subject_iri:
            return subject_iri

        if doi:
            return f"https://doi.org/{doi}"

        if source_url and source_url.startswith(("http://", "https://")):
            return source_url

        return ""

    def _create_assay_table(
        self,
        graph: Graph,
        subject: Node,
        source_url: str | None = None,
        doi: str | None = None,
    ) -> ArcTable:
        url = self._resolve_assay_url(graph, subject, source_url, doi)

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

        publisher_name = self._resolve_publisher_label(graph, subject)
        if publisher_name:
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
