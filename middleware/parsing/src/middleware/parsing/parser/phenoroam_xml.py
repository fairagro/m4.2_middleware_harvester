"""Inline PhenoRoam ``pr:metadataDataset`` PayloadParser."""

from __future__ import annotations

from typing import ClassVar, override
from xml.etree.ElementTree import Element, ParseError

from defusedxml.ElementTree import fromstring  # type: ignore[import-untyped]

from middleware.harvester.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, XmlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
from middleware.payload.kinds import PayloadKind
from middleware.payload.parsed_payload import ParsedPayload
from middleware.payload.phenoroam.models import (
    PhenoroamBBox,
    PhenoroamPerson,
    PhenoroamRecord,
    PhenoroamStudyBlock,
)


@PayloadParser.register(ParserType.phenoroam_xml)
class PhenoroamXmlParser(PayloadParser):
    """Parse inline PhenoRoam XML into a ``phenoroam_record`` payload."""

    produces: ClassVar[PayloadKind] = PayloadKind.phenoroam_record
    _PR_NS: ClassVar[str] = "http://www.phenorob.de/"
    _NS: ClassVar[dict[str, str]] = {"pr": "http://www.phenorob.de/"}

    @override
    async def parse(
        self,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: object,
    ) -> ParsedPayload:
        """Parse inline ``pr:metadataDataset`` without requiring an HTTP client."""
        _ = client, config
        if not isinstance(discovery_result, XmlDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")
        xml = discovery_result.xml.strip() if discovery_result.xml else ""
        if not xml:
            raise ParserError(f"Missing PhenoRoam XML metadata for {discovery_result.identifier}")

        record = self.parse_phenoroam_xml(xml, discovery_identifier=discovery_result.identifier)
        identifier = (record.item_uuid or "").strip() or discovery_result.identifier.strip()
        if not identifier.strip():
            raise ParserError(f"PhenoRoam record has no stable identifier for {discovery_result.identifier}")
        return ParsedPayload(kind=PayloadKind.phenoroam_record, value=record, identifier=identifier)

    def parse_phenoroam_xml(self, xml: str, *, discovery_identifier: str) -> PhenoroamRecord:
        """Parse ``pr:metadataDataset`` XML into ``PhenoroamRecord``."""
        try:
            root = fromstring(xml)
        except ParseError as exc:
            raise ParserError(f"Failed to parse PhenoRoam XML for {discovery_identifier}: {exc}") from exc
        return self._parse_root(root, discovery_identifier=discovery_identifier)

    @staticmethod
    def _local(tag: str) -> str:
        if tag.startswith("{"):
            return tag.rsplit("}", 1)[-1]
        if ":" in tag:
            return tag.split(":", 1)[-1]
        return tag

    @staticmethod
    def _text(el: Element | None) -> str | None:
        if el is None or el.text is None:
            return None
        stripped = el.text.strip()
        return stripped or None

    @classmethod
    def _find_text(cls, parent: Element, path: str) -> str | None:
        return cls._text(parent.find(path, cls._NS))

    @classmethod
    def _findall(cls, parent: Element, path: str) -> list[Element]:
        return list(parent.findall(path, cls._NS))

    @classmethod
    def _parse_person(cls, block: Element) -> PhenoroamPerson | None:
        person_el = block.find("pr:blockPerson", cls._NS)
        if person_el is None:
            return None
        name = cls._find_text(person_el, "pr:itemName")
        if not name:
            return None
        return PhenoroamPerson(
            name=name,
            email=cls._find_text(person_el, "pr:itemEmail"),
            affiliation=cls._find_text(person_el, "pr:itemAffiliation"),
        )

    @classmethod
    def _parse_study(cls, root: Element) -> PhenoroamStudyBlock | None:
        study_el = root.find(".//pr:blockStudy", cls._NS)
        if study_el is None:
            return None
        inv_el = study_el.find("pr:blockInvestigation", cls._NS)
        return PhenoroamStudyBlock(
            study_title=cls._find_text(study_el, "pr:itemTitle"),
            study_description=cls._find_text(study_el, "pr:itemDescription"),
            investigation_title=cls._find_text(inv_el, "pr:itemTitle") if inv_el is not None else None,
            investigation_description=(cls._find_text(inv_el, "pr:itemDescription") if inv_el is not None else None),
        )

    @classmethod
    def _parse_bbox(cls, root: Element) -> PhenoroamBBox | None:
        bbox_el = root.find(".//pr:blockBBox", cls._NS)
        if bbox_el is None:
            return None
        bbox = PhenoroamBBox(
            west=cls._find_text(bbox_el, "pr:itemBBoxWest"),
            east=cls._find_text(bbox_el, "pr:itemBBoxEast"),
            south=cls._find_text(bbox_el, "pr:itemBBoxSouth"),
            north=cls._find_text(bbox_el, "pr:itemBBoxNorth"),
        )
        if not any((bbox.west, bbox.east, bbox.south, bbox.north)):
            return None
        return bbox

    @classmethod
    def _parse_contacts(cls, root: Element, path: str) -> list[PhenoroamPerson]:
        people: list[PhenoroamPerson] = []
        for block in cls._findall(root, path):
            person = cls._parse_person(block)
            if person is not None:
                people.append(person)
        return people

    @classmethod
    def _parse_datafile_links(cls, root: Element) -> list[str]:
        links: list[str] = []
        for link_el in cls._findall(root, ".//pr:listDatafiles/pr:blockDatafile/pr:itemLink"):
            value = cls._text(link_el)
            if value:
                links.append(value)
        return links

    @classmethod
    def _texts(cls, root: Element, path: str) -> list[str]:
        return [value for el in cls._findall(root, path) if (value := cls._text(el))]

    @classmethod
    def _parse_root(cls, root: Element, *, discovery_identifier: str) -> PhenoroamRecord:
        if cls._local(root.tag) != "metadataDataset":
            raise ParserError(
                f"Expected pr:metadataDataset root for {discovery_identifier}, got {cls._local(root.tag)!r}"
            )
        return PhenoroamRecord(
            item_uuid=cls._find_text(root, ".//pr:itemUUID"),
            title=cls._find_text(root, ".//pr:itemDataSetTitle"),
            description=cls._find_text(root, ".//pr:itemDataSetDescription"),
            keywords=cls._texts(root, ".//pr:listKeywords/pr:itemKeyword"),
            responsible_contacts=cls._parse_contacts(root, ".//pr:blockResponsibleContact"),
            other_contacts=cls._parse_contacts(root, ".//pr:blockOtherContact"),
            study=cls._parse_study(root),
            datafile_links=cls._parse_datafile_links(root),
            thumbnail_url=cls._find_text(root, ".//pr:itemThumbnail"),
            license_text=cls._find_text(root, ".//pr:itemLicense"),
            how_to_cite=cls._find_text(root, ".//pr:itemHowToCite"),
            funded_by=cls._find_text(root, ".//pr:itemFundedBy"),
            download_information=cls._find_text(root, ".//pr:itemDownloadInformation"),
            core_projects=cls._texts(root, ".//pr:listCoreprojects/pr:itemCoreProject"),
            bbox=cls._parse_bbox(root),
            md_change_date=cls._find_text(root, ".//pr:itemMDChangeDate"),
        )
