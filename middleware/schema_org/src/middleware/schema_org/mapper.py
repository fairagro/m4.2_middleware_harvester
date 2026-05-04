"""Mapper module for converting Schema.org Dataset objects to ARC objects.

This module provides the SchemaOrgMapper class, which maps Schema.org metadata
to ARC Investigation, Study, Assay, and related objects.
"""

import re
from collections.abc import Sequence
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
from rdflib import Graph  # type: ignore[import-untyped]

from .models import Organization, Person as SchemaOrgPerson, SchemaOrgDataset
from .schema_org_mapper import SchemaOrgMapper


class GeneralSchemaOrgMapper(SchemaOrgMapper):
    """Maps SchemaOrgDataset to ARC objects using the general Schema.org mapping rules."""

    def map_graph(self, graph: Graph) -> str:
        """Map an RDF graph to a serialized RO-Crate JSON-LD string."""
        dataset = self._parse_graph(graph)
        arc = self.map_dataset(dataset)
        return cast(str, arc.ToROCrateJsonString())

    def _parse_graph(self, graph: Graph) -> SchemaOrgDataset:
        """Convert the supplied RDF graph into a SchemaOrgDataset object."""
        raise NotImplementedError(
            "GeneralSchemaOrgMapper requires a graph-to-SchemaOrgDataset parser before it can be used."  # noqa: E501
        )

    def map_dataset(self, dataset: SchemaOrgDataset) -> ARC:
        """Map SchemaOrgDataset to ARC."""
        # 1. Create Investigation
        investigation = self.map_investigation(dataset)

        # 2. Create Study
        study = self.map_study(dataset)
        investigation.AddStudy(study)

        # 3. Create Assay
        assay = self.map_assay(dataset)
        investigation.AddAssay(assay)
        study.RegisterAssay(assay.Identifier)

        # 4. Wrap in ARC
        arc = ARC.from_arc_investigation(investigation)

        return arc

    def _to_identifier_slug(self, title: str) -> str:
        """Convert a title to a machine-readable identifier slug."""
        if not title:
            return "untitled"
        # Lowercase, replace non-alphanumeric with underscores
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower())
        # Remove leading/trailing underscores
        slug = slug.strip("_")
        # Truncate to a reasonable length
        return slug[:80]

    def _dataset_title(self, dataset: SchemaOrgDataset, default: str = "") -> str:
        """Return the dataset title or a fallback string."""
        if dataset.identification and dataset.identification.name:
            return dataset.identification.name
        return default

    def _extract_doi(self, dataset: SchemaOrgDataset) -> str | None:
        """Extract DOI from dataset identifier or id field."""
        if (
            dataset.identification
            and dataset.identification.identifier
            and isinstance(dataset.identification.identifier, str)
            and dataset.identification.identifier.startswith("10.")
        ):
            return dataset.identification.identifier
        if dataset.identification and dataset.identification.id:
            # Check if id contains a DOI URL and return the DOI prefix only
            doi_match = re.search(r"doi\.org/(?P<doi>10\.[^/?#]+)", dataset.identification.id, re.IGNORECASE)
            if doi_match:
                return doi_match.group("doi")
            if dataset.identification.id.startswith("10."):
                return dataset.identification.id
        return None

    def map_person(self, person: SchemaOrgPerson | Organization) -> Person | None:
        """Map Schema.org Person or Organization to ARC Person."""
        if isinstance(person, Organization):
            return self._map_organization(person)

        if not (person.given_name or person.family_name or person.name):
            return None

        first_name, last_name = self._split_person_name(person)
        address = self._format_person_address(person)

        arc_person = Person.create(
            last_name=last_name,
            first_name=first_name,
            email=person.email,
            address=address,
        )

        if person.url:
            arc_person.Comments.append(Comment.create("URL", person.url))

        return arc_person

    def _map_organization(self, organization: Organization) -> Person | None:
        if not organization.name:
            return None
        return Person.create(
            last_name=organization.name,
            first_name="",
            affiliation=organization.name,
        )

    def _split_person_name(self, person: SchemaOrgPerson) -> tuple[str, str]:
        first_name = person.given_name or ""
        last_name = person.family_name or ""

        if not first_name and not last_name and person.name:
            name_parts = person.name.split(" ")
            last_name = name_parts[-1] if name_parts else ""
            first_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else person.name

        return first_name, last_name

    def _format_person_address(self, person: SchemaOrgPerson) -> str | None:
        if not person.address:
            return None
        if isinstance(person.address, str):
            return person.address

        address_parts = []
        if person.address.street_address:
            address_parts.append(person.address.street_address)
        if person.address.postal_code:
            address_parts.append(person.address.postal_code)
        if person.address.address_country:
            address_parts.append(person.address.address_country)

        return ", ".join(address_parts) if address_parts else None

    def map_investigation(self, dataset: SchemaOrgDataset) -> ArcInvestigation:
        """Map to ArcInvestigation with metadata fields."""
        # Get identifier - prefer DOI or @id
        identifier = (
            self._extract_doi(dataset)
            or (dataset.identification.id if dataset.identification else None)
            or self._to_identifier_slug(self._dataset_title(dataset))
        )

        # Clean identifier for filesystem compatibility
        if identifier and ("://" in identifier or "/" in identifier):
            identifier = self._to_identifier_slug(self._dataset_title(dataset)) or identifier.split("/")[-1]

        title = (dataset.identification.name if dataset.identification else None) or "Untitled Dataset"
        description = (dataset.identification.description if dataset.identification else None) or ""
        submission_date = (
            (dataset.dates.date_published if dataset.dates else None)
            or (dataset.dates.date_modified if dataset.dates else None)
            or ""
        )

        inv = ArcInvestigation.create(
            identifier=identifier, title=title, description=description, submission_date=submission_date
        )

        self._add_contacts(inv, dataset)
        self._add_publications(inv, dataset)
        self._add_comments(inv, dataset)
        self._add_ontology_sources(inv)

        return inv

    def _add_ontology_sources(self, inv: ArcInvestigation) -> None:
        """Add ontology source references."""
        # Add Schema.org as ontology source
        inv.OntologySourceReferences.append(
            OntologySourceReference.create(
                name="SCHEMAORG",
                file="https://schema.org/",
                version="",
                description="Schema.org vocabulary for structured data",
            )
        )

        # Add common ontology sources
        common_ontologies = [
            ("NCIT", "http://purl.obolibrary.org/obo/ncit.owl", "NCI Thesaurus"),
            ("EDAM", "http://edamontology.org", "EDAM Bioinformatics Ontology"),
        ]

        for name, url, desc in common_ontologies:
            inv.OntologySourceReferences.append(
                OntologySourceReference.create(
                    name=name,
                    file=url,
                    version="",
                    description=desc,
                )
            )

    def _add_contacts(self, inv: ArcInvestigation, dataset: SchemaOrgDataset) -> None:
        """Add all contacts to the investigation."""
        self._add_author_contacts(inv, dataset.agents.creator if dataset.agents else None)
        self._add_author_contacts(inv, dataset.agents.author if dataset.agents else None, skip_existing=True)
        self._add_role_contacts(inv, dataset.agents.contributor if dataset.agents else None, "contributor")
        if dataset.agents and dataset.agents.publisher:
            self._add_role_contact(inv, dataset.agents.publisher, "publisher")

    def _add_author_contacts(
        self,
        inv: ArcInvestigation,
        contacts: Sequence[SchemaOrgPerson | Organization] | None,
        skip_existing: bool = False,
    ) -> None:
        if not contacts:
            return

        for contact in contacts:
            if skip_existing and self._contact_exists(inv, contact):
                continue

            person = self.map_person(contact)
            if not person:
                continue

            person.Roles.append(OntologyAnnotation(name="author"))
            inv.Contacts.append(person)

    def _add_role_contacts(
        self, inv: ArcInvestigation, contacts: Sequence[SchemaOrgPerson | Organization] | None, role_name: str
    ) -> None:
        if not contacts:
            return

        for contact in contacts:
            person = self.map_person(contact)
            if not person:
                continue
            person.Roles.append(OntologyAnnotation(name=role_name))
            inv.Contacts.append(person)

    def _add_role_contact(self, inv: ArcInvestigation, contact: SchemaOrgPerson | Organization, role_name: str) -> None:
        person = self.map_person(contact)
        if not person:
            return
        person.Roles.append(OntologyAnnotation(name=role_name))
        inv.Contacts.append(person)

    def _contact_exists(self, inv: ArcInvestigation, author: SchemaOrgPerson | Organization) -> bool:
        if isinstance(author, SchemaOrgPerson):
            author_first = author.given_name or ""
            author_last = author.family_name or ""
            for existing in inv.Contacts:
                if existing.FirstName == author_first and existing.LastName == author_last:
                    return True
            return False

        author_name = author.name or ""
        return any(existing.LastName == author_name for existing in inv.Contacts)

    def _add_publications(self, inv: ArcInvestigation, dataset: SchemaOrgDataset) -> None:
        """Add publications from dataset."""
        doi = self._extract_doi(dataset)
        if doi:
            # Format authors string
            authors_list = [p for p in inv.Contacts if any(role.Name == "author" for role in p.Roles)]
            author_strings = []
            for p in authors_list:
                first_initial = f"{p.FirstName[0]}." if p.FirstName else ""
                author_strings.append(f"{p.LastName}, {first_initial}")
            authors_str = "; ".join(author_strings) if author_strings else None

            pub = Publication.create(
                title=(dataset.identification.name if dataset.identification else None) or "Untitled",
                authors=authors_str,
                doi=doi,
            )
            inv.Publications.append(pub)

        # Handle citations
        if dataset.metadata and dataset.metadata.citation:
            citations = (
                [dataset.metadata.citation]
                if isinstance(dataset.metadata.citation, str)
                else list(dataset.metadata.citation)
            )

            for citation in citations:
                if citation and citation not in [p.DOI for p in inv.Publications]:
                    pub = Publication.create(
                        title=citation[:200],  # Truncate long citations
                        authors=None,
                    )
                    inv.Publications.append(pub)

    def _add_comments(self, inv: ArcInvestigation, dataset: SchemaOrgDataset) -> None:
        """Add metadata-level comments to the investigation."""
        comments = self._generate_comments(dataset)
        for comment in comments:
            inv.Comments.append(comment)

    def _generate_comments(self, dataset: SchemaOrgDataset) -> list[Comment]:
        """Generate metadata-level comments from dataset fields."""
        comments = []

        # Simple string-based fields
        keywords_value = dataset.metadata.keywords if dataset.metadata else None
        fields = [
            (
                "Keywords",
                keywords_value
                if isinstance(keywords_value, str)
                else ", ".join(keywords_value)
                if keywords_value
                else None,
            ),
            (
                "License",
                dataset.metadata.license if dataset.metadata and isinstance(dataset.metadata.license, str) else None,
            ),
            ("Language", dataset.metadata.in_language if dataset.metadata else None),
            ("Version", dataset.metadata.version if dataset.metadata else None),
            ("URL", dataset.distribution_info.url if dataset.distribution_info else None),
        ]
        for label, value in fields:
            if value:
                comments.append(Comment.create(label, value))

        # Add conformsTo info
        if dataset.distribution_info and dataset.distribution_info.conforms_to:
            profile_id = (
                dataset.distribution_info.conforms_to.get("@id", "")
                if isinstance(dataset.distribution_info.conforms_to, dict)
                else ""
            )
            if profile_id:
                comments.append(Comment.create("Conforms To", profile_id))

        # Add distribution info
        if dataset.distribution_info and dataset.distribution_info.distributions:
            for dist in dataset.distribution_info.distributions[:3]:  # Limit to first 3
                if isinstance(dist, dict):
                    encoding_format = dist.get("encodingFormat", "")
                    content_url = dist.get("contentUrl", "")
                    if encoding_format or content_url:
                        comments.append(Comment.create("Distribution", f"{encoding_format}: {content_url}"))

        return comments

    def map_study(self, dataset: SchemaOrgDataset) -> ArcStudy:
        """Map to ArcStudy with process-oriented protocols."""
        identifier = self._to_identifier_slug(self._dataset_title(dataset, "dataset"))
        title = (dataset.identification.name if dataset.identification else None) or "Untitled Dataset"
        description = (
            dataset.identification.description if dataset.identification else None
        ) or "Imported from Schema.org metadata"

        study = ArcStudy.create(
            identifier=identifier,
            title=title,
            description=description,
            submission_date=(dataset.dates.date_published if dataset.dates else None),
        )

        # Add protocols
        # Protocol 1: Data Collection (if keywords or description available)
        collection_protocol = self._create_data_collection_protocol(dataset)
        if collection_protocol:
            study.AddTable(collection_protocol)

        # Protocol 2: Data Processing (always created)
        processing_protocol = self._create_data_processing_protocol(dataset)
        if processing_protocol:
            study.AddTable(processing_protocol)

        return study

    def _create_data_collection_protocol(self, dataset: SchemaOrgDataset) -> ArcTable | None:
        """Create Data Collection protocol if metadata available."""
        metadata_keywords = dataset.metadata.keywords if dataset.metadata else None
        metadata_description = dataset.identification.description if dataset.identification else None
        if not (metadata_keywords or metadata_description):
            return None

        table = ArcTable.init("Data Collection")

        headers = []
        cells = []

        # Keywords as parameters
        if metadata_keywords:
            keywords_str = metadata_keywords if isinstance(metadata_keywords, str) else ", ".join(metadata_keywords)
            headers.append(CompositeHeader.parameter(OntologyAnnotation(name="Keywords")))
            cells.append(CompositeCell.term(OntologyAnnotation(name=keywords_str)))

        if headers:
            table.AddColumn(
                CompositeHeader.input(IOType.source()),
                [CompositeCell.free_text("Research Subject")],
            )
            for i, header in enumerate(headers):
                table.AddColumn(header, [cells[i]])
            table.AddColumn(
                CompositeHeader.output(IOType.sample()),
                [CompositeCell.free_text("")],
            )
            return table
        return None

    def _create_data_processing_protocol(self, dataset: SchemaOrgDataset) -> ArcTable | None:
        """Create Data Processing protocol (keine free_text-Cells für IOType.data())."""
        table = ArcTable.init("Data Processing")

        # Data input column: use create_data_from_string (ISA-konform wie INSPIRE)
        table.AddColumn(
            CompositeHeader.input(IOType.data()),
            [CompositeCell.create_data_from_string("Raw Data")],
        )

        # Add processing description from metadata
        processing_note = "Data processing and publication according to Schema.org metadata standard"
        if dataset.agents and dataset.agents.publisher:
            processing_note += f" | Publisher: {dataset.agents.publisher.name}"

        table.AddColumn(
            CompositeHeader.parameter(OntologyAnnotation(name="Processing Description")),
            [CompositeCell.term(OntologyAnnotation(name=processing_note))],
        )

        # Data output column: use create_data_from_string (ISA-konform wie INSPIRE)
        table.AddColumn(
            CompositeHeader.output(IOType.data()),
            [CompositeCell.create_data_from_string("Published Dataset")],
        )

        return table

    def map_assay(self, dataset: SchemaOrgDataset) -> ArcAssay:
        """Map to ArcAssay with annotation table."""
        identifier = self._to_identifier_slug(self._dataset_title(dataset, "dataset"))
        title = (dataset.identification.name if dataset.identification else None) or "Untitled Dataset"

        measurement_type = OntologyAnnotation(name="Data Collection")
        technology_type = OntologyAnnotation(name="Data Repository")

        assay = ArcAssay.create(
            identifier=identifier,
            title=title,
            measurement_type=measurement_type,
            technology_type=technology_type,
        )

        # Set Technology Platform
        assay.TechnologyPlatform = OntologyAnnotation(name="Schema.org Data Repository")

        # Add the annotation table
        assay.AddTable(self._create_assay_table(dataset))

        return assay

    def _create_assay_table(self, dataset: SchemaOrgDataset) -> ArcTable:
        """Create the assay annotation table.

        Columns:
        - Input [Source Name]                : "Dataset Source" (always present)
        - Output [URI]                       : dataset URL or identifier
        - Comment [License]                  : license information if available
        - Comment [Publisher]                : publisher information
        """
        # Determine Output URI
        output_uri = (
            (dataset.distribution_info.url if dataset.distribution_info else None)
            or (dataset.identification.id if dataset.identification else None)
            or f"{self._to_identifier_slug(self._dataset_title(dataset))}_dataset"
        )

        table = ArcTable.init("Measurement")
        table.AddColumn(CompositeHeader.input(IOType.source()), [CompositeCell.free_text("Dataset Source")])
        table.AddColumn(
            CompositeHeader.output(IOType.of_string("URI")),
            [CompositeCell.free_text(output_uri)],
        )

        # Add license comment
        if dataset.metadata and dataset.metadata.license:
            license_value = (
                dataset.metadata.license if isinstance(dataset.metadata.license, str) else str(dataset.metadata.license)
            )
            table.AddColumn(
                CompositeHeader.comment("License"),
                [CompositeCell.free_text(license_value)],
            )

        # Add publisher comment
        if dataset.agents and dataset.agents.publisher:
            table.AddColumn(
                CompositeHeader.comment("Publisher"),
                [CompositeCell.free_text(dataset.agents.publisher.name or "Unknown Publisher")],
            )

        # Add language comment
        if dataset.metadata and dataset.metadata.in_language:
            table.AddColumn(
                CompositeHeader.comment("Language"),
                [CompositeCell.free_text(dataset.metadata.in_language)],
            )

        return table
