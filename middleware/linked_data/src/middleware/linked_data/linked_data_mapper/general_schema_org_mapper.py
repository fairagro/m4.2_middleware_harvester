"""Mapper module for converting Schema.org RDF graphs to ARC objects.

THIS IS AN EXAMPLE IMPLEMENTATION. A PRODUCTION-READY IMPLEMENTATION WOULD
REQUIRE A DEFINITIVE SPEC HOW TO MAP SCHEMA.ORG TO ARC IN A MEANINGFUL WAY.
Field access goes through StableGraph / ResourceView; ARC assembly stays here.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
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
    Person,
    Publication,
)
from arctrl.py.Core.ontology_source_reference import OntologySourceReference
from rdflib import Graph, Literal, Namespace, URIRef  # type: ignore[import-untyped]
from rdflib.term import Node

from middleware.harvester.person_contacts import require_nonempty_person_given_names
from middleware.harvester.person_names import split_display_name
from middleware.harvester.plugin_base import HarvestedArc

from ..config import PayloadType
from .linked_data_mapper import LinkedDataMapper, MappingContext
from .stable_graph import SCHEMA_ORG_NAMESPACES, ResourceView, StableGraph, http_iri


@dataclass(frozen=True)
class _IdentifierPlan:
    """Resolved investigation identifier and DOI metadata for one Dataset."""

    investigation_id: str
    publication_doi: str | None
    alternate_dois: tuple[str, ...]


@LinkedDataMapper.register(PayloadType.schema_org_general)
class GeneralSchemaOrgMapper(LinkedDataMapper):
    """Maps a Schema.org RDF graph to ARC objects.

    RDF reads use the ``StableGraph`` passed into ``_map_graph`` (via a per-call
    ``_SchemaOrgRun``); identifier cascade and publisher policy stay here.
    """

    SCHEMA_URIS = [
        Namespace("https://schema.org/"),
        Namespace("http://schema.org/"),
    ]

    @override
    def _stable_wrap(self, graph: Graph) -> StableGraph:
        """Wrap with Schema.org http/https term aliases and ``schema:name`` labels."""
        return StableGraph.wrap(
            graph,
            term_namespaces=SCHEMA_ORG_NAMESPACES,
            label_predicates=tuple(ns.name for ns in SCHEMA_ORG_NAMESPACES),
        )

    @override
    def _map_graph(self, graph: Graph, context: MappingContext, stable: StableGraph) -> Iterable[HarvestedArc]:
        """Map an RDF graph to harvested ARCs with composition counts.

        Yields one HarvestedArc per schema:Dataset entity in the graph.
        """
        _ = graph  # Access via ``stable`` (call-scoped wrap).
        dataset_views = stable.subjects_of_types(*(schema.Dataset for schema in self.SCHEMA_URIS))
        if not dataset_views:
            raise ValueError("Graph does not contain a Schema.org Dataset entity")

        # Page-level harvest_source_id / source_url is one catalog unit. When a page
        # embeds multiple Datasets, prefer per-subject graph identifiers so ARCs do
        # not collide on Investigation.identifier (see schemaorg-to-arc-mapping).
        use_page_harvest_id = len(dataset_views) == 1
        for dataset in dataset_views:
            arc = _SchemaOrgRun(self, stable).map_arc(
                dataset.node,
                context,
                use_page_harvest_id=use_page_harvest_id,
            )
            yield HarvestedArc.from_arctrl(arc)


@dataclass(frozen=True)
class _SchemaOrgRun:
    """One ``map_graph`` call: owns the StableGraph explicitly (not on the mapper)."""

    mapper: GeneralSchemaOrgMapper
    stable: StableGraph

    def view(self, subject: Node) -> ResourceView:
        """ResourceView for ``subject`` on this call's StableGraph."""
        return self.stable.view(subject)

    def map_arc(
        self,
        subject: Node,
        context: MappingContext,
        *,
        use_page_harvest_id: bool = True,
    ) -> ARC:
        title = self._require_dataset_title(subject)
        identifier_plan = self._plan_investigation_identifier(
            subject,
            context,
            use_page_harvest_id=use_page_harvest_id,
        )
        publication_doi = identifier_plan.publication_doi

        investigation = self._map_investigation(subject, title=title, identifier_plan=identifier_plan)
        study = self._map_study(subject, title=title)
        investigation.AddStudy(study)
        assay = self._map_assay(subject, context, title=title, doi=publication_doi)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)
        return ARC.from_arc_investigation(investigation)

    def _require_dataset_title(self, subject: Node) -> str:
        """Return a non-empty ``schema:name``, or fail closed (no Untitled fallback)."""
        title = (self.view(subject)["name"] or "").strip()
        if not title:
            raise ValueError("Schema.org Dataset has no non-empty schema:name; refusing Untitled fallback")
        return title

    def _study_assay_identifier(self, title: str) -> str:
        identifier = self.mapper.to_identifier_slug(title)
        if identifier is None:
            raise ValueError(f"Schema.org Dataset title {title!r} does not yield a usable Study/Assay identifier slug")
        return identifier

    def _canonical_http_identifier(self, subject: Node, term: str) -> str | None:
        iris = [iri for obj in self.view(subject).schema_objects(term) if (iri := http_iri(obj))]
        if not iris:
            return None
        return min(iris, key=lambda iri: (iri.casefold(), iri))

    def _resolve_graph_url_identifier(self, subject: Node) -> str | None:
        for term in ("url", "sameAs"):
            identifier = self._canonical_http_identifier(subject, term)
            if identifier:
                return self.mapper.sanitize_identifier(identifier)
        subject_iri = http_iri(subject)
        return self.mapper.sanitize_identifier(subject_iri) if subject_iri else None

    def _plan_investigation_identifier(
        self,
        subject: Node,
        context: MappingContext,
        *,
        use_page_harvest_id: bool = True,
    ) -> _IdentifierPlan:
        all_dois = self.view(subject).schema_dois("identifier")
        publication_doi = self.mapper.pick_canonical_doi(all_dois)
        alternate_dois = tuple(doi for doi in all_dois if doi != publication_doi) if publication_doi else ()

        if use_page_harvest_id:
            harvest_id = self.mapper.resolve_harvest_source_identifier(context)
            if harvest_id:
                return _IdentifierPlan(harvest_id, publication_doi, alternate_dois)

        graph_id = self._resolve_graph_url_identifier(subject)
        if graph_id:
            return _IdentifierPlan(graph_id, publication_doi, alternate_dois)

        if publication_doi:
            return _IdentifierPlan(publication_doi, publication_doi, alternate_dois)

        raise ValueError(
            "Schema.org Dataset has no stable identifier "
            "(DOI, http(s) URL, or source URL); refusing blank-node identifier"
        )

    def _map_investigation(
        self,
        subject: Node,
        *,
        title: str,
        identifier_plan: _IdentifierPlan,
    ) -> ArcInvestigation:
        plan = identifier_plan
        identifier = plan.investigation_id

        description = self.view(subject)["description"] or ""
        submission_date = self.view(subject)["datePublished"] or self.view(subject)["dateModified"] or ""

        inv = ArcInvestigation.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=submission_date,
        )

        self._add_contacts(inv, subject)
        self._add_publications(inv, subject, title=title, doi=plan.publication_doi)
        self._add_alternate_identifier_comments(inv, plan.alternate_dois)
        self._add_investigation_comments(inv, subject)
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

    def _add_contacts(self, inv: ArcInvestigation, subject: Node) -> None:
        creators = sorted(
            self.view(subject).schema_objects("creator"),
            key=self._contact_sort_key,
        )
        for node in creators:
            self._append_contact(inv, node, "author")

        authors = sorted(
            self.view(subject).schema_objects("author"),
            key=self._contact_sort_key,
        )
        for node in authors:
            if not self._contact_exists(inv, node):
                self._append_contact(inv, node, "author")

        contributors = sorted(
            self.view(subject).schema_objects("contributor"),
            key=self._contact_sort_key,
        )
        for node in contributors:
            self._append_contact(inv, node, "contributor")
        require_nonempty_person_given_names(inv)

    def _contact_sort_key(self, node: Node) -> tuple[str, str, str, tuple[int, str]]:
        """Stable sort key: family, given, display name, then node identity without BNode labels."""
        given, family = self._person_names(node)
        display = str(node).strip() if isinstance(node, Literal) else self.view(node)["name"] or ""
        return (
            (family or "").casefold(),
            (given or "").casefold(),
            display.casefold(),
            self.stable.sort_key(node),
        )

    def _append_contact(self, inv: ArcInvestigation, node: Node, role: str) -> None:
        if not isinstance(node, Literal) and self.view(node).schema_is_type("Organization"):
            self._append_organization_comment(inv, node, role)
            return
        person = self._node_to_person(node)
        if person is None:
            return
        person.Roles.append(OntologyAnnotation(name=role))
        inv.Contacts.append(person)

    def _append_organization_comment(self, inv: ArcInvestigation, node: Node, role: str) -> bool:
        """Append Organization comment(s). Return True if a comment was emitted."""
        org_name = self.view(node)["name"]
        if not org_name:
            if isinstance(node, URIRef):
                org_name = str(node)
            else:
                return False
        comment_name = "Publisher" if role == "publisher" else role.capitalize()
        inv.Comments.append(Comment.create(comment_name, org_name))
        org_url = self.view(node)["url"] or (str(node) if isinstance(node, URIRef) else None)
        if org_url and org_url != org_name:
            inv.Comments.append(Comment.create(f"{comment_name} URL", org_url))
        return True

    def _contact_exists(self, inv: ArcInvestigation, node: Node) -> bool:
        given, family = self._person_names(node)
        if given is None:
            return False
        return any(c.FirstName == given and c.LastName == family for c in inv.Contacts)

    def _person_names(self, node: Node) -> tuple[str | None, str]:
        """Return ``(given, family)`` or ``(None, ...)`` when given name would be empty."""
        if isinstance(node, Literal):
            parts = split_display_name(str(node))
            return parts.given, parts.family

        if self.view(node).schema_is_type("Organization"):
            return None, self.view(node)["name"] or ""

        given = (self.view(node)["givenName"] or "").strip()
        family = (self.view(node)["familyName"] or "").strip()
        name = self.view(node)["name"]

        if not given and name:
            parts = split_display_name(name)
            if parts.given:
                given = parts.given
            if not family:
                family = parts.family

        if not given:
            return None, family
        return given, family

    def _node_to_person(self, node: Node) -> Person | None:
        if isinstance(node, Literal):
            parts = split_display_name(str(node))
            if parts.given is None:
                if parts.family:
                    raise ValueError(f"Person contact must have a non-empty given name (last_name={parts.family!r})")
                return None
            return Person.create(last_name=parts.family, first_name=parts.given)

        if self.view(node).schema_is_type("Organization"):
            return None

        given, family = self._person_names(node)
        email = self.view(node)["email"]
        url = self.view(node)["url"]

        if given is None:
            if family or self.view(node)["name"]:
                raise ValueError(f"Person contact must have a non-empty given name (last_name={family!r})")
            return None

        affiliation = self._extract_affiliation(node)
        address = self._extract_address(node)
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

    def _extract_affiliation(self, node: Node) -> str | None:
        aff_node = self.view(node).schema_object_node("affiliation")
        if aff_node is None:
            return None
        if isinstance(aff_node, Literal):
            return str(aff_node).strip() or None
        return self.view(aff_node)["name"]

    def _extract_address(self, node: Node) -> str | None:
        addr_node = self.view(node).schema_object_node("address")
        if addr_node is None:
            return None
        if isinstance(addr_node, Literal):
            return str(addr_node)
        parts = [
            self.view(addr_node)["streetAddress"],
            self.view(addr_node)["postalCode"],
            self.view(addr_node)["addressCountry"],
        ]
        return ", ".join(p for p in parts if p) or None

    def _add_publications(self, inv: ArcInvestigation, subject: Node, *, title: str, doi: str | None) -> None:
        if doi:
            authors = [p for p in inv.Contacts if any(r.Name == "author" for r in p.Roles)]
            author_strs: list[str] = []
            for p in authors:
                if p.FirstName and p.LastName:
                    author_strs.append(f"{p.FirstName[0]}. {p.LastName}")
                elif p.LastName:
                    author_strs.append(p.LastName)
                elif p.FirstName:
                    author_strs.append(p.FirstName)

            inv.Publications.append(
                Publication.create(
                    title=title,
                    authors="; ".join(author_strs) if author_strs else None,
                    doi=doi,
                )
            )

        for citation in self.view(subject).schema_texts("citation"):
            if citation and citation not in [p.DOI for p in inv.Publications]:
                inv.Publications.append(Publication.create(title=citation[:200], authors=None))

    def _add_investigation_comments(self, inv: ArcInvestigation, subject: Node) -> None:
        keywords = self.view(subject).schema_texts("keywords")
        if keywords:
            inv.Comments.append(Comment.create("Keywords", ", ".join(keywords)))

        for label, term in [
            ("License", "license"),
            ("Language", "inLanguage"),
            ("Version", "version"),
            ("URL", "url"),
        ]:
            value = self.view(subject).schema_text(term)
            if value:
                inv.Comments.append(Comment.create(label, value))

        self._add_publisher_comment(inv, subject)

        conforms_to = self.view(subject).schema_object_node("conformsTo")
        conforms_text = self.stable.object_text(conforms_to)
        if conforms_text:
            inv.Comments.append(Comment.create("Conforms To", conforms_text))

        for dist in self.view(subject).schema_resources("distribution"):
            content_url = dist["contentUrl"] or ""
            if not content_url:
                continue
            encoding = dist["encodingFormat"] or ""
            label = f"{encoding}: {content_url}" if encoding else content_url
            inv.Comments.append(Comment.create("Distribution", label))

    def _iter_preferred_publishers(self, subject: Node) -> Iterator[Node]:
        """Yield publisher resources first (stable order), then optional literal."""
        objects = list(self.view(subject).schema_objects("publisher"))
        non_literals = sorted(
            (obj for obj in objects if not isinstance(obj, Literal)),
            key=self.stable.sort_key,
        )
        yield from non_literals
        lit = self.view(subject).schema_literal("publisher")
        if lit is not None:
            yield Literal(lit.value)

    def _add_publisher_comment(self, inv: ArcInvestigation, subject: Node) -> None:
        for publisher_node in self._iter_preferred_publishers(subject):
            if isinstance(publisher_node, Literal):
                inv.Comments.append(Comment.create("Publisher", str(publisher_node)))
                return
            if self.view(publisher_node).schema_is_type("Organization"):
                if self._append_organization_comment(inv, publisher_node, "publisher"):
                    return
                continue
            pub_name = self.view(publisher_node)["name"]
            if pub_name:
                inv.Comments.append(Comment.create("Publisher", pub_name))
                return
            if isinstance(publisher_node, URIRef):
                inv.Comments.append(Comment.create("Publisher", str(publisher_node)))
                return

    def _resolve_publisher_label(self, subject: Node) -> str | None:
        """Stable publisher display label for protocol/assay notes."""
        for node in self._iter_preferred_publishers(subject):
            if isinstance(node, Literal):
                return str(node)
            name = self.view(node)["name"]
            if name:
                return name
            if isinstance(node, URIRef):
                return str(node)
        return None

    def _map_study(self, subject: Node, *, title: str) -> ArcStudy:
        identifier = self._study_assay_identifier(title)
        description = self.view(subject)["description"] or "Imported from Schema.org metadata"

        study = ArcStudy.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=self.view(subject)["datePublished"],
        )

        collection_table = self._create_data_collection_table(subject)
        if collection_table:
            study.AddTable(collection_table)
        study.AddTable(self._create_data_processing_table(subject))
        return study

    def _create_data_collection_table(self, subject: Node) -> ArcTable | None:
        keywords = self.view(subject).schema_texts("keywords")
        if not keywords:
            return None

        table = ArcTable.init("Data Collection")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Research Subject")],
        )
        table.AddColumn(
            CompositeHeader.parameter(OntologyAnnotation(name="Keywords")),
            [CompositeCell.term(OntologyAnnotation(name=", ".join(keywords)))],
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

        note = "Data processing and publication according to Schema.org metadata standard"
        publisher_name = self._resolve_publisher_label(subject)
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

    def _map_assay(self, subject: Node, context: MappingContext, *, title: str, doi: str | None = None) -> ArcAssay:
        identifier = self._study_assay_identifier(title)

        assay = ArcAssay.create(
            identifier=identifier,
            title=title,
            measurement_type=OntologyAnnotation(name="Data Collection"),
            technology_type=OntologyAnnotation(name="Data Repository"),
        )
        assay.TechnologyPlatform = OntologyAnnotation(name="Schema.org Data Repository")
        assay.AddTable(self._create_assay_table(subject, context, doi=doi))
        return assay

    def _resolve_assay_url(self, subject: Node, context: MappingContext, doi: str | None) -> str:
        """Resolve the landing-page URL for the Measurement output URI cell."""
        for term in ("url", "sameAs"):
            iri = self._canonical_http_identifier(subject, term)
            if iri:
                return iri

        subject_iri = http_iri(subject)
        if subject_iri:
            return subject_iri

        if doi:
            return f"https://doi.org/{doi}"

        if context.source_url and context.source_url.startswith(("http://", "https://")):
            return context.source_url

        return ""

    def _create_assay_table(
        self,
        subject: Node,
        context: MappingContext,
        *,
        doi: str | None = None,
    ) -> ArcTable:
        url = self._resolve_assay_url(subject, context, doi)

        table = ArcTable.init("Measurement")
        table.AddColumn(
            CompositeHeader.input(IOType.source()),
            [CompositeCell.free_text("Dataset Source")],
        )
        table.AddColumn(
            CompositeHeader.output(IOType.of_string("URI")),
            [CompositeCell.free_text(url)],
        )

        license_val = self.view(subject)["license"]
        if license_val:
            table.AddColumn(
                CompositeHeader.comment("License"),
                [CompositeCell.free_text(license_val)],
            )

        publisher_name = self._resolve_publisher_label(subject)
        if publisher_name:
            table.AddColumn(
                CompositeHeader.comment("Publisher"),
                [CompositeCell.free_text(publisher_name)],
            )

        language = self.view(subject)["inLanguage"]
        if language:
            table.AddColumn(
                CompositeHeader.comment("Language"),
                [CompositeCell.free_text(language)],
            )

        dist_entries: list[str] = []
        for dist in self.view(subject).schema_resources("distribution"):
            content_url = dist["contentUrl"] or ""
            if not content_url:
                continue
            encoding = dist["encodingFormat"] or ""
            dist_entries.append(f"{encoding}: {content_url}" if encoding else content_url)
        if dist_entries:
            # One cell per assay row (joined), matching other Measurement columns.
            table.AddColumn(
                CompositeHeader.comment("Distribution"),
                [CompositeCell.free_text("; ".join(dist_entries))],
            )

        return table
