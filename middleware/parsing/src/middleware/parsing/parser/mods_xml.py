"""MyCoRe object XML → ``mods_record`` PayloadParser."""

from __future__ import annotations

from typing import ClassVar, override

import lxml.etree  # type: ignore[import-untyped]

from middleware.contracts.nice_http_client import NiceHttpClient
from middleware.parsing.discovery import DiscoveryResult, UrlDiscoveryResult
from middleware.parsing.errors import ParserError
from middleware.parsing.parser.parser import PayloadParser
from middleware.parsing.parser_type import ParserType
from middleware.parsing.xml_hardening import HARDENED_XML_PARSER
from middleware.payload.kinds import PayloadKind
from middleware.payload.mods.models import ModsName, ModsRecord
from middleware.payload.parsed_payload import ParsedPayload

_MODS_NS = "http://www.loc.gov/mods/v3"
_XLINK_HREF = "{http://www.w3.org/1999/xlink}href"


@PayloadParser.register(ParserType.mods_xml)
class ModsXmlParser(PayloadParser):
    """Fetch MyCoRe object XML and extract embedded MODS into ``mods_record``."""

    produces: ClassVar[PayloadKind] = PayloadKind.mods_record

    @override
    async def parse(
        self,
        discovery_result: DiscoveryResult,
        client: NiceHttpClient | None,
        config: object,
    ) -> ParsedPayload:
        """Fetch object XML for a URL discovery result and return a ``mods_record``."""
        _ = config
        if not isinstance(discovery_result, UrlDiscoveryResult):
            raise ValueError(f"Unsupported discovery result type: {type(discovery_result).__name__}")
        if client is None:
            raise ValueError("ModsXmlParser requires an HTTP client; client must not be None.")

        response = await client.get_with_policy(discovery_result.url)
        if response.is_error:
            raise ParserError(
                f"Failed to fetch MyCoRe object XML HTTP {response.status_code} for {discovery_result.url}"
            )

        record = self.parse_object_xml(
            response.content,
            discovery_identifier=discovery_result.identifier,
            harvest_source_id=discovery_result.harvest_source_id,
        )
        identifier = (record.object_id or "").strip() or discovery_result.identifier.strip()
        if not identifier.strip():
            raise ParserError(f"MODS record has no stable identifier for {discovery_result.url}")
        return ParsedPayload(kind=PayloadKind.mods_record, value=record, identifier=identifier)

    def parse_object_xml(
        self,
        xml: bytes | str,
        *,
        discovery_identifier: str,
        harvest_source_id: str | None = None,
    ) -> ModsRecord:
        """Parse MyCoRe object XML bytes/text into ``ModsRecord``."""
        try:
            root = lxml.etree.fromstring(
                xml if isinstance(xml, bytes) else xml.encode("utf-8"), parser=HARDENED_XML_PARSER
            )
        except lxml.etree.XMLSyntaxError as exc:
            raise ParserError(f"Failed to parse MyCoRe object XML for {discovery_identifier}: {exc}") from exc

        mods_root = self._find_mods_root(root)
        if mods_root is None:
            raise ParserError(f"No mods:mods subtree in MyCoRe object XML for {discovery_identifier}")

        object_id = self._object_id(root) or (harvest_source_id or "").strip() or None
        return ModsRecord(
            object_id=object_id,
            title=self._first_title(mods_root),
            abstract=self._first_abstract(mods_root),
            doi=self._doi(mods_root),
            date_issued=self._date_issued(mods_root),
            license_uri=self._license_uri(mods_root),
            language=self._language(mods_root),
            names=self._names(mods_root),
            keywords=self._keywords(mods_root),
            datafile_names=self._datafile_names(root),
        )

    @staticmethod
    def _local(tag: object) -> str:
        if not isinstance(tag, str):
            return ""
        if tag.startswith("{"):
            return tag.rsplit("}", 1)[-1]
        if ":" in tag:
            return tag.split(":", 1)[-1]
        return tag

    @classmethod
    def _find_mods_root(cls, root: lxml.etree._Element) -> lxml.etree._Element | None:
        for node in root.iter():
            if cls._local(node.tag) == "mods":
                return node
        return None

    @classmethod
    def _object_id(cls, root: lxml.etree._Element) -> str | None:
        for attr in ("ID", "id"):
            value = root.get(attr)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @classmethod
    def _text(cls, el: lxml.etree._Element | None) -> str | None:
        if el is None:
            return None
        # Prefer direct text; fall back to concatenated descendant text for mixed content.
        chunks = [t.strip() for t in el.itertext() if t and t.strip()]
        if not chunks:
            return None
        return " ".join(chunks)

    @classmethod
    def _first_title(cls, mods: lxml.etree._Element) -> str | None:
        for title_info in mods.iter(f"{{{_MODS_NS}}}titleInfo"):
            title_el = title_info.find(f"{{{_MODS_NS}}}title")
            text = cls._text(title_el)
            if text:
                return text
        return None

    @classmethod
    def _first_abstract(cls, mods: lxml.etree._Element) -> str | None:
        for abstract in mods.iter(f"{{{_MODS_NS}}}abstract"):
            text = cls._text(abstract)
            if text:
                return text
        return None

    @classmethod
    def _doi(cls, mods: lxml.etree._Element) -> str | None:
        for ident in mods.iter(f"{{{_MODS_NS}}}identifier"):
            if (ident.get("type") or "").lower() != "doi":
                continue
            text = cls._text(ident)
            if text:
                return text
        return None

    @classmethod
    def _date_issued(cls, mods: lxml.etree._Element) -> str | None:
        for date in mods.iter(f"{{{_MODS_NS}}}dateIssued"):
            text = cls._text(date)
            if text:
                return text
        return None

    @classmethod
    def _license_uri(cls, mods: lxml.etree._Element) -> str | None:
        for access in mods.iter(f"{{{_MODS_NS}}}accessCondition"):
            access_type = (access.get("type") or "").lower()
            if "use and reproduction" not in access_type and "license" not in access_type:
                continue
            href = access.get(_XLINK_HREF) or access.get("xlink:href")
            if isinstance(href, str) and href.strip():
                return href.strip()
            text = cls._text(access)
            if text:
                return text
        return None

    @classmethod
    def _language(cls, mods: lxml.etree._Element) -> str | None:
        for term in mods.iter(f"{{{_MODS_NS}}}languageTerm"):
            text = cls._text(term)
            if text:
                return text
        return None

    @classmethod
    def _names(cls, mods: lxml.etree._Element) -> list[ModsName]:
        names: list[ModsName] = []
        for name_el in mods.iter(f"{{{_MODS_NS}}}name"):
            role_codes = [
                code
                for role_term in name_el.iter(f"{{{_MODS_NS}}}roleTerm")
                if (role_term.get("type") or "").lower() == "code"
                for code in [(cls._text(role_term) or "").strip()]
                if code
            ]
            given = None
            family = None
            for part in name_el.findall(f"{{{_MODS_NS}}}namePart"):
                part_type = (part.get("type") or "").lower()
                text = cls._text(part)
                if not text:
                    continue
                if part_type == "given":
                    given = text
                elif part_type == "family":
                    family = text
            orcid = None
            gnd = None
            for ident in name_el.findall(f"{{{_MODS_NS}}}nameIdentifier"):
                ident_type = (ident.get("type") or "").lower()
                text = cls._text(ident)
                if not text:
                    continue
                if ident_type == "orcid":
                    orcid = text
                elif ident_type == "gnd":
                    gnd = text
            names.append(
                ModsName(
                    display_form=cls._text(name_el.find(f"{{{_MODS_NS}}}displayForm")),
                    given=given,
                    family=family,
                    affiliation=cls._text(name_el.find(f"{{{_MODS_NS}}}affiliation")),
                    orcid=orcid,
                    gnd=gnd,
                    role_codes=role_codes,
                    name_type=name_el.get("type"),
                )
            )
        return names

    @classmethod
    def _keywords(cls, mods: lxml.etree._Element) -> list[str]:
        keywords: list[str] = []
        for topic in mods.iter(f"{{{_MODS_NS}}}topic"):
            text = cls._text(topic)
            if text:
                keywords.append(text)
        return keywords

    @classmethod
    def _datafile_names(cls, root: lxml.etree._Element) -> list[str]:
        names: list[str] = []
        for node in root.iter():
            if cls._local(node.tag) != "maindoc":
                continue
            text = cls._text(node)
            if text:
                names.append(text)
        return names
