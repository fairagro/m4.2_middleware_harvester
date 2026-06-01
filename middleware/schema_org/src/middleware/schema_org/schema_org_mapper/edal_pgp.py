"""EDAL-PGP mapper: overrides general mapper for EDAL-PGP data quirks."""

from datetime import datetime

from arctrl import ArcInvestigation, ArcStudy, Comment, Person
from rdflib import Graph, Literal, Namespace
from rdflib.term import Node

from ..config import PayloadType
from .general import GeneralSchemaOrgMapper
from .schema_org_mapper import SchemaOrgMapper

DCTERMS = Namespace("http://purl.org/dc/terms/")

EDAL_DATE_FORMAT = "%a %b %d %H:%M:%S %Z %Y"
STUDY_DESC_MAX = 500
MIN_ADDRESS_PARTS = 3
PLACEHOLDER_LICENSE_URL = "$licenseURL"


@SchemaOrgMapper.register(PayloadType.edal_pgp)
class EdalPgpMapper(GeneralSchemaOrgMapper):
    """Maps EDAL-PGP schema.org graphs to ARC RO-Crate."""

    def _extract_orcid(self, graph: Graph, node: Node) -> str | None:
        schema = self._active_schema or self.SCHEMA_URIS[0]
        identifier_node = self._obj(graph, node, schema.identifier)
        if identifier_node is None or isinstance(identifier_node, Literal):
            return None
        prop_id = self._str(graph, identifier_node, schema.propertyID)
        value = self._str(graph, identifier_node, schema.value)
        if prop_id and prop_id.lower() == "orcid" and value:
            return value
        return None

    def _parse_edal_date(self, date_str: str) -> str:
        try:
            dt = datetime.strptime(date_str, EDAL_DATE_FORMAT)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return date_str

    def _node_to_person(self, graph: Graph, node: Node) -> Person | None:
        person = super()._node_to_person(graph, node)
        if person is not None:
            orcid = self._extract_orcid(graph, node)
            if orcid and not any(c.Name == "ORCID" for c in person.Comments):
                person.Comments.append(Comment.create("ORCID", orcid))
        return person

    def _extract_address(self, graph: Graph, node: Node) -> str | None:
        addr_node = self._obj(graph, node, self._schema().address)
        if addr_node is None:
            return None
        if isinstance(addr_node, Literal):
            return self._parse_string_address(str(addr_node))
        addr_type = self._obj(graph, addr_node, self._schema().addressCountry)
        if addr_type is not None:
            return super()._extract_address(graph, node)
        return self._parse_string_address(str(addr_node))

    def _parse_string_address(self, raw: str) -> str:
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) >= MIN_ADDRESS_PARTS:
            street = parts[0]
            postal = parts[-2] if parts[-2].startswith("D-") else parts[-2]
            country = parts[-1]
            return f"{street}, {postal}, {country}"
        return raw

    def _is_person_seen(
        self,
        graph: Graph,
        node: Node,
        seen_orcids: set[str],
        seen_names: set[tuple[str, str]],
    ) -> bool:
        orcid = self._extract_orcid(graph, node)
        given = self._str(graph, node, self._schema().givenName) or ""
        family = self._str(graph, node, self._schema().familyName) or ""

        if orcid:
            if orcid in seen_orcids:
                return True
            seen_orcids.add(orcid)
        elif given or family:
            key = (given, family)
            if key in seen_names:
                return True
            seen_names.add(key)
        return False

    def _add_contacts(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        seen_orcids: set[str] = set()
        seen_names: set[tuple[str, str]] = set()

        for predicate, role in [
            (self._schema().author, "author"),
            (self._schema().creator, "author"),
            (self._schema().contributor, "contributor"),
        ]:
            for node in graph.objects(subject, predicate):
                if self._is_person_seen(graph, node, seen_orcids, seen_names):
                    continue
                person = self._node_to_person(graph, node)
                if person is None:
                    continue
                person.Roles.append(self._role_annotation(role))
                inv.Contacts.append(person)
        publisher_node = self._obj(graph, subject, self._schema().publisher)
        if publisher_node is not None:
            self._append_contact(inv, graph, publisher_node, "publisher")

    def _role_annotation(self, name: str) -> object:
        from arctrl import OntologyAnnotation

        return OntologyAnnotation(name=name)

    def _split_keywords(self, keywords_value: object) -> list[str]:
        if isinstance(keywords_value, str):
            return [kw.strip() for kw in keywords_value.split(",") if kw.strip()]
        return []

    def _add_license_comment(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        license_val = self._str(graph, subject, self._schema().license)
        if not license_val:
            return
        if PLACEHOLDER_LICENSE_URL in license_val:
            inv.Comments.append(Comment.create("License", "URL not provided"))
        else:
            inv.Comments.append(Comment.create("License", license_val))

    def _add_conforms_to_comment(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        for ns in [self._schema().conformsTo, DCTERMS.conformsTo]:
            value = self._obj(graph, subject, ns)
            if value is not None:
                inv.Comments.append(Comment.create("Conforms To", str(value)))
                break

    def _add_distribution_comments(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        for dist_node in graph.objects(subject, self._schema().distribution):
            if isinstance(dist_node, Literal):
                continue
            encoding = self._str(graph, dist_node, self._schema().encodingFormat) or ""
            content_url = self._str(graph, dist_node, self._schema().contentUrl) or ""
            if encoding or content_url:
                inv.Comments.append(Comment.create("Distribution", f"{encoding}: {content_url}"))

    def _add_investigation_comments(self, inv: ArcInvestigation, graph: Graph, subject: Node) -> None:
        keywords = self._str(graph, subject, self._schema().keywords)
        if keywords:
            terms = self._split_keywords(keywords)
            if terms:
                inv.Comments.append(Comment.create("Keywords", ", ".join(terms)))

        for label, predicate in [
            ("Language", self._schema().inLanguage),
            ("Version", self._schema().version),
            ("URL", self._schema().url),
        ]:
            value = self._str(graph, subject, predicate)
            if value:
                inv.Comments.append(Comment.create(label, value))

        self._add_license_comment(inv, graph, subject)
        self._add_conforms_to_comment(inv, graph, subject)
        self._add_distribution_comments(inv, graph, subject)

    def _map_study(self, graph: Graph, subject: Node) -> ArcStudy:
        title = self._str(graph, subject, self._schema().name) or "Untitled Dataset"
        identifier = self._to_identifier_slug(title) or "dataset"
        description = self._str(graph, subject, self._schema().description) or "Imported from Schema.org metadata"
        if len(description) > STUDY_DESC_MAX:
            description = description[:STUDY_DESC_MAX]

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

    def _map_investigation(self, graph: Graph, subject: Node) -> ArcInvestigation:
        inv = super()._map_investigation(graph, subject)

        raw_date = self._str(graph, subject, self._schema().datePublished)
        if raw_date:
            parsed = self._parse_edal_date(raw_date)
            if parsed != raw_date:
                inv.SubmissionDate = parsed

        return inv
