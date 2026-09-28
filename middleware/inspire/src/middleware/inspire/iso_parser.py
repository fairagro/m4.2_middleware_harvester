"""ISO 19139 record parser for INSPIRE metadata."""

import contextlib
import logging
from typing import cast

from owslib.iso import MD_DataIdentification, MD_Metadata  # type: ignore[import-untyped]

from middleware.inspire.errors import SemanticError
from middleware.inspire.models import (
    ConformanceResult,
    Contact,
    DistributionFormat,
    InspireDate,
    InspireRecord,
    OnlineResource,
    ReferenceSystem,
    ResourceIdentifier,
    SpatialResolutionDistance,
)
from middleware.inspire.value_bounds import (
    MAX_LIST_ITEMS,
    MAX_STR_LONG,
    MAX_STR_MEDIUM,
    MAX_STR_SHORT,
    bounded_str,
    truncate,
    valid_http_url,
)

logger = logging.getLogger(__name__)


class IsoParser:
    """Parser for OWSLib MD_Metadata objects into InspireRecord domain objects."""

    def parse_record(self, iso: MD_Metadata, record_uuid: str) -> InspireRecord:
        """Parse an OWSLib MD_Metadata object into an InspireRecord."""
        # Ensure identifier is always an actual string from ISO metadata
        if not iso.identifier or not isinstance(iso.identifier, str):
            raise SemanticError(f"Record {record_uuid} is missing a valid identifier (gmd:fileIdentifier).")

        identifier = truncate(iso.identifier, MAX_STR_MEDIUM)
        identification = self._extract_identification(iso)

        return InspireRecord(
            # Core identification (existing fields)
            identifier=identifier,
            title=self._extract_title(identification),
            abstract=self._extract_abstract(identification),
            date_stamp=iso.datestamp,
            keywords=self._extract_identification_list("keywords", identification),
            topic_categories=self._extract_identification_list("topiccategory", identification),
            contacts=self._extract_contacts(iso),
            lineage=self._extract_lineage(iso),
            spatial_extent=self._extract_spatial_extent(iso),
            temporal_extent=self._extract_temporal_extent(iso),
            constraints=self._extract_constraints(iso),
            # Metadata-level fields (new)
            parent_identifier=bounded_str(getattr(iso, "parentidentifier", None), MAX_STR_MEDIUM),
            language=bounded_str(getattr(iso, "language", None) or getattr(iso, "languagecode", None), MAX_STR_SHORT),
            charset=bounded_str(getattr(iso, "charset", None), MAX_STR_SHORT),
            hierarchy=bounded_str(getattr(iso, "hierarchy", None), MAX_STR_SHORT),
            metadata_standard_name=bounded_str(getattr(iso, "stdname", None), MAX_STR_MEDIUM),
            metadata_standard_version=bounded_str(getattr(iso, "stdver", None), MAX_STR_SHORT),
            dataset_uri=valid_http_url(getattr(iso, "dataseturi", None)),
            # Identification - Core (new)
            alternate_title=self._extract_identification_str("alternatetitle", identification),
            resource_identifiers=self._extract_resource_identifiers(identification),
            edition=self._extract_identification_str("edition", identification, MAX_STR_SHORT),
            purpose=self._extract_identification_str("purpose", identification),
            status=self._extract_identification_str("status", identification, MAX_STR_SHORT),
            resource_language=self._extract_resource_language(identification),
            graphic_overviews=self._extract_graphic_overviews(identification),
            # Identification - Dates (new)
            dates=self._extract_dates(identification),
            # Identification - Resolution (new)
            spatial_resolution_denominators=self._extract_resolution_denominators(identification),
            spatial_resolution_distances=self._extract_resolution_distances(identification),
            # Identification - Contacts by role (new)
            creators=self._extract_contacts_by_role(identification, "originator"),
            publishers=self._extract_contacts_by_role(identification, "publisher"),
            contributors=self._extract_contacts_by_role(identification, "author"),
            # Constraints (detailed, new)
            access_constraints=self._extract_access_constraints(identification),
            use_constraints=self._extract_use_constraints(identification),
            classification=self._extract_classification(identification),
            other_constraints=self._extract_other_constraints(identification),
            other_constraints_url=self._extract_other_constraints_url(identification),
            # Distribution (new)
            distribution_formats=self._extract_distribution_formats(iso),
            online_resources=self._extract_online_resources(iso),
            # Data Quality (new)
            conformance_results=self._extract_conformance_results(iso),
            lineage_url=self._extract_lineage_url(iso),
            # Reference System (new)
            reference_systems=self._extract_reference_systems(iso),
            # Supplemental (new)
            supplemental_information=self._extract_identification_str(
                "supplementalinformation", identification, MAX_STR_LONG
            ),
        )

    @staticmethod
    def _extract_identification(iso: MD_Metadata) -> MD_DataIdentification | None:
        """Extract identification info from ISO record."""
        if isinstance(iso.identification, list) and iso.identification:
            return cast(MD_DataIdentification, iso.identification[0])
        elif iso.identification:
            return cast(MD_DataIdentification, iso.identification)
        return None

    @staticmethod
    def _extract_title(identification: MD_DataIdentification | None) -> str:
        """Extract title from ISO record."""
        if identification is None or getattr(identification, "title", None) is None:
            raise SemanticError("Record is missing a title in its identification section.")
        if not isinstance(identification.title, str):
            raise SemanticError("Record title is not a string.")
        return truncate(identification.title, MAX_STR_MEDIUM)

    @staticmethod
    def _extract_abstract(identification: MD_DataIdentification | None) -> str:
        """Extract abstract from ISO record."""
        if identification is None or getattr(identification, "abstract", None) is None:
            raise SemanticError("Record is missing an abstract in its identification section.")
        if not isinstance(identification.abstract, str):
            raise SemanticError("Record abstract is not a string.")
        return truncate(identification.abstract, MAX_STR_LONG)

    @staticmethod
    def _extract_identification_str(
        item: str, identification: MD_DataIdentification | None, max_len: int = MAX_STR_MEDIUM
    ) -> str | None:
        """Extract a string attribute from ISO record."""
        if identification is None:
            return None
        value = getattr(identification, item, None)
        # Ensure we only return actual strings, not MagicMock or other objects
        if value and isinstance(value, str):
            return truncate(value, max_len)
        return None

    @staticmethod
    def _extract_identification_list(item: str, identification: MD_DataIdentification | None) -> list[str]:
        """Extract a list attribute from ISO record."""
        result: list[str] = []
        if identification is None:
            return result
        if hasattr(identification, item):
            attr = getattr(identification, item)
            if isinstance(attr, list):
                result.extend([truncate(i, MAX_STR_MEDIUM) for i in attr[:MAX_LIST_ITEMS] if isinstance(i, str)])
            elif isinstance(attr, str):
                result.append(truncate(attr, MAX_STR_MEDIUM))
        return result

    def _extract_contacts(self, iso: MD_Metadata) -> list[Contact]:
        """Extract contacts from ISO record."""
        contacts = []
        if iso.contact:
            contacts.extend(self._format_contacts(iso.contact, "metadata"))
        identification = self._extract_identification(iso)
        if identification and identification.contact:
            contacts.extend(self._format_contacts(identification.contact, "resource"))
        return contacts

    @staticmethod
    def _format_contacts(contact_list: list, contact_type: str) -> list[Contact]:
        """Format contact list."""
        return [
            Contact(
                name=bounded_str(c.name, MAX_STR_MEDIUM),
                organization=bounded_str(c.organization, MAX_STR_MEDIUM),
                email=c.email,
                role=c.role,
                type=contact_type,
            )
            for c in contact_list[:MAX_LIST_ITEMS]
        ]

    @staticmethod
    def _extract_lineage(iso: MD_Metadata) -> str | None:
        """Extract lineage from ISO record."""
        if iso.dataquality and iso.dataquality.lineage:
            lineage = iso.dataquality.lineage
            if isinstance(lineage, str):
                return truncate(lineage, MAX_STR_LONG)
            if hasattr(lineage, "statement"):
                statement = lineage.statement
                return truncate(statement, MAX_STR_LONG) if isinstance(statement, str) else None
        return None

    def _extract_spatial_extent(self, iso: MD_Metadata) -> list[float] | None:
        """Extract spatial extent from ISO record."""
        identification = self._extract_identification(iso)
        if identification and identification.bbox:
            bbox = identification.bbox
            if bbox and all(hasattr(bbox, attr) for attr in ["minx", "miny", "maxx", "maxy"]):
                try:
                    minx = getattr(bbox, "minx", None)
                    miny = getattr(bbox, "miny", None)
                    maxx = getattr(bbox, "maxx", None)
                    maxy = getattr(bbox, "maxy", None)
                    if all(v is not None for v in [minx, miny, maxx, maxy]):
                        return [
                            float(cast(float, minx)),
                            float(cast(float, miny)),
                            float(cast(float, maxx)),
                            float(cast(float, maxy)),
                        ]
                except (ValueError, TypeError):
                    return None
        return None

    def _extract_temporal_extent(self, iso: MD_Metadata) -> tuple[str | None, str | None] | None:
        """Extract temporal extent from ISO record."""
        identification = self._extract_identification(iso)
        if identification and hasattr(identification, "temporalextent_start") and identification.temporalextent_start:
            return (identification.temporalextent_start, getattr(identification, "temporalextent_end", None))
        return None

    def _extract_constraints(self, iso: MD_Metadata) -> list[str]:
        """Extract constraints from ISO record."""
        constraints = []
        identification = self._extract_identification(iso)
        if identification:
            # Check for resourceconstraint (singular) which is the standard OWSLib attribute
            resource_constraints = getattr(identification, "resourceconstraint", None)
            if resource_constraints:
                if isinstance(resource_constraints, list):
                    for c in resource_constraints[:MAX_LIST_ITEMS]:
                        if hasattr(c, "use_limitation") and c.use_limitation:
                            constraints.extend(c.use_limitation)
                elif hasattr(resource_constraints, "use_limitation") and resource_constraints.use_limitation:
                    constraints.extend(resource_constraints.use_limitation)
        return [truncate(c, MAX_STR_MEDIUM) for c in constraints[:MAX_LIST_ITEMS] if isinstance(c, str)]

    # === Extended INSPIRE Field Extraction ===

    @staticmethod
    def _extract_resource_identifiers(identification: MD_DataIdentification | None) -> list[ResourceIdentifier]:
        """Extract resource identifiers (DOI, ISBN, etc.) from citation/identifier."""
        identifiers: list[ResourceIdentifier] = []
        if identification is None:
            return identifiers

        # uricode and uricodespace are lists in OWSLib
        uricode_list = getattr(identification, "uricode", [])
        uricodespace_list = getattr(identification, "uricodespace", [])

        # Zip them together, padding shorter list with None
        max_len = min(max(len(uricode_list), len(uricodespace_list)), MAX_LIST_ITEMS)
        for i in range(max_len):
            code = uricode_list[i] if i < len(uricode_list) else None
            codespace = uricodespace_list[i] if i < len(uricodespace_list) else None
            if code:
                identifiers.append(
                    ResourceIdentifier(
                        code=truncate(code, MAX_STR_MEDIUM),
                        codespace=bounded_str(codespace, MAX_STR_MEDIUM),
                        url=valid_http_url(code),
                    )
                )
        return identifiers

    @staticmethod
    def _extract_dates(identification: MD_DataIdentification | None) -> list[InspireDate]:
        """Extract citation dates with types (creation, publication, revision)."""
        dates: list[InspireDate] = []
        if identification is None:
            return dates

        ci_dates = getattr(identification, "date", [])
        for ci_date in ci_dates[:MAX_LIST_ITEMS]:
            if hasattr(ci_date, "date") and hasattr(ci_date, "type"):
                dates.append(InspireDate(date=truncate(ci_date.date, MAX_STR_SHORT), datetype=ci_date.type))
        return dates

    @staticmethod
    def _extract_resource_language(identification: MD_DataIdentification | None) -> list[str]:
        """Extract resource language(s)."""
        langs: list[str] = []
        if identification is None:
            return langs

        # OWSLib has both resourcelanguage and resourcelanguagecode
        langs.extend(getattr(identification, "resourcelanguagecode", []))
        langs.extend(getattr(identification, "resourcelanguage", []))
        return [
            truncate(lang, MAX_STR_SHORT) for lang in langs[:MAX_LIST_ITEMS] if lang and isinstance(lang, str)
        ]  # Filter out None/empty/non-string

    @staticmethod
    def _extract_graphic_overviews(identification: MD_DataIdentification | None) -> list[str]:
        """Extract thumbnail/preview image URLs."""
        if identification is None:
            return []
        urls = getattr(identification, "graphicoverview", [])
        valid_urls = [valid_http_url(u) for u in urls[:MAX_LIST_ITEMS]]
        return [u for u in valid_urls if u is not None]

    @staticmethod
    def _extract_resolution_denominators(identification: MD_DataIdentification | None) -> list[int]:
        """Extract spatial resolution as scale denominators.

        A malformed denominator is dropped, not fatal: unlike a missing identifier/title/
        abstract, one bad scale value does not make the whole record unusable.
        """
        if identification is None:
            return []
        denoms = getattr(identification, "denominators", [])
        result: list[int] = []
        for d in denoms[:MAX_LIST_ITEMS]:
            if not d:
                continue
            with contextlib.suppress(ValueError, TypeError):
                result.append(int(d))
        return result

    @staticmethod
    def _extract_resolution_distances(
        identification: MD_DataIdentification | None,
    ) -> list[SpatialResolutionDistance]:
        """Extract spatial resolution as distances with units."""
        if identification is None:
            return []

        distances = []
        distance_vals = getattr(identification, "distance", [])
        uom_vals = getattr(identification, "uom", [])

        for i, dist in enumerate(distance_vals[:MAX_LIST_ITEMS]):
            uom = uom_vals[i] if i < len(uom_vals) else "m"
            if dist:
                with contextlib.suppress(ValueError, TypeError):
                    distances.append(
                        SpatialResolutionDistance(value=float(dist), uom=truncate(uom or "m", MAX_STR_SHORT))
                    )
        return distances

    def _extract_contacts_by_role(self, identification: MD_DataIdentification | None, role_name: str) -> list[Contact]:
        """Extract contacts filtered by specific role."""
        contacts: list[Contact] = []
        if identification is None:
            return contacts

        # Get role-specific lists from OWSLib
        if role_name == "originator":
            contact_list = getattr(identification, "creator", [])
        elif role_name == "publisher":
            contact_list = getattr(identification, "publisher", [])
        elif role_name == "author":
            contact_list = getattr(identification, "contributor", [])
        else:
            return contacts

        return self._format_contacts(contact_list, "resource")

    @staticmethod
    def _extract_access_constraints(identification: MD_DataIdentification | None) -> list[str]:
        """Extract access constraints."""
        if identification is None:
            return []
        constraints = getattr(identification, "accessconstraints", [])
        return [truncate(c, MAX_STR_MEDIUM) for c in constraints[:MAX_LIST_ITEMS] if isinstance(c, str) and c]

    @staticmethod
    def _extract_use_constraints(identification: MD_DataIdentification | None) -> list[str]:
        """Extract use constraints."""
        if identification is None:
            return []
        constraints = getattr(identification, "useconstraints", [])
        return [truncate(c, MAX_STR_MEDIUM) for c in constraints[:MAX_LIST_ITEMS] if isinstance(c, str) and c]

    @staticmethod
    def _extract_classification(identification: MD_DataIdentification | None) -> list[str]:
        """Extract classification constraints."""
        if identification is None:
            return []
        constraints = getattr(identification, "classification", [])
        return [truncate(c, MAX_STR_MEDIUM) for c in constraints[:MAX_LIST_ITEMS] if isinstance(c, str) and c]

    @staticmethod
    def _extract_other_constraints(identification: MD_DataIdentification | None) -> list[str]:
        """Extract other constraints text."""
        if identification is None:
            return []
        constraints = getattr(identification, "otherconstraints", [])
        return [truncate(c, MAX_STR_MEDIUM) for c in constraints[:MAX_LIST_ITEMS] if isinstance(c, str) and c]

    @staticmethod
    def _extract_other_constraints_url(identification: MD_DataIdentification | None) -> list[str]:
        """Extract other constraints URLs."""
        if identification is None:
            return []
        urls = getattr(identification, "otherconstraints_url", [])
        valid_urls = [valid_http_url(u) for u in urls[:MAX_LIST_ITEMS]]
        return [u for u in valid_urls if u is not None]

    @staticmethod
    def _extract_distribution_formats(iso: MD_Metadata) -> list[DistributionFormat]:
        """Extract distribution format information."""
        formats: list[DistributionFormat] = []
        dist = getattr(iso, "distribution", None)
        if dist is None:
            return formats

        if hasattr(dist, "format") and dist.format:
            formats.append(
                DistributionFormat(
                    name=truncate(dist.format, MAX_STR_MEDIUM),
                    version=bounded_str(getattr(dist, "version", None), MAX_STR_SHORT),
                    specification=bounded_str(getattr(dist, "specification", None), MAX_STR_MEDIUM),
                    name_url=valid_http_url(getattr(dist, "format_url", None)),
                    version_url=valid_http_url(getattr(dist, "version_url", None)),
                    specification_url=valid_http_url(getattr(dist, "specification_url", None)),
                )
            )
        return formats

    @staticmethod
    def _extract_online_resources(iso: MD_Metadata) -> list[OnlineResource]:
        """Extract online resources (download links, service endpoints)."""
        resources: list[OnlineResource] = []
        dist = getattr(iso, "distribution", None)
        if dist is None:
            return resources

        online_list = getattr(dist, "online", [])
        for ol in online_list[:MAX_LIST_ITEMS]:
            url = valid_http_url(getattr(ol, "url", None))
            if url is None:
                # OnlineResource.url is required; an invalid-scheme/oversized URL means
                # the whole entry is dropped rather than constructed with a bad URL.
                continue
            resources.append(
                OnlineResource(
                    url=url,
                    protocol=bounded_str(getattr(ol, "protocol", None), MAX_STR_SHORT),
                    protocol_url=valid_http_url(getattr(ol, "protocol_url", None)),
                    name=bounded_str(getattr(ol, "name", None), MAX_STR_MEDIUM),
                    name_url=valid_http_url(getattr(ol, "name_url", None)),
                    description=bounded_str(getattr(ol, "description", None), MAX_STR_LONG),
                    description_url=valid_http_url(getattr(ol, "description_url", None)),
                    function=bounded_str(getattr(ol, "function", None), MAX_STR_SHORT),
                )
            )
        return resources

    @staticmethod
    def _extract_conformance_results(iso: MD_Metadata) -> list[ConformanceResult]:
        """Extract data quality conformance results."""
        results: list[ConformanceResult] = []
        dq = getattr(iso, "dataquality", None)
        if dq is None:
            return results

        titles = getattr(dq, "conformancetitle", [])
        title_urls = getattr(dq, "conformancetitle_url", [])
        dates = getattr(dq, "conformancedate", [])
        datetypes = getattr(dq, "conformancedatetype", [])
        degrees = getattr(dq, "conformancedegree", [])

        max_len = min(max(len(titles), len(dates), len(degrees)) if titles or dates or degrees else 0, MAX_LIST_ITEMS)
        for i in range(max_len):
            title = titles[i] if i < len(titles) else None
            if title:
                results.append(
                    ConformanceResult(
                        specification_title=truncate(title, MAX_STR_MEDIUM),
                        specification_title_url=valid_http_url(title_urls[i] if i < len(title_urls) else None),
                        specification_date=bounded_str(dates[i] if i < len(dates) else None, MAX_STR_SHORT),
                        specification_datetype=bounded_str(datetypes[i] if i < len(datetypes) else None, MAX_STR_SHORT),
                        degree=bounded_str(degrees[i] if i < len(degrees) else None, MAX_STR_SHORT),
                    )
                )
        return results

    @staticmethod
    def _extract_lineage_url(iso: MD_Metadata) -> str | None:
        """Extract lineage URL if lineage uses gmx:Anchor."""
        dq = getattr(iso, "dataquality", None)
        if dq is None:
            return None
        value = getattr(dq, "lineage_url", None)
        return valid_http_url(value)

    @staticmethod
    def _extract_reference_systems(iso: MD_Metadata) -> list[ReferenceSystem]:
        """Extract coordinate reference system(s)."""
        systems: list[ReferenceSystem] = []
        rs = getattr(iso, "referencesystem", None)
        if rs is None:
            return systems

        if hasattr(rs, "code") and rs.code:
            systems.append(
                ReferenceSystem(
                    code=truncate(rs.code, MAX_STR_MEDIUM),
                    code_url=valid_http_url(getattr(rs, "code_url", None)),
                    codespace=bounded_str(getattr(rs, "codeSpace", None), MAX_STR_MEDIUM),
                    codespace_url=valid_http_url(getattr(rs, "codeSpace_url", None)),
                    version=bounded_str(getattr(rs, "version", None), MAX_STR_SHORT),
                    version_url=valid_http_url(getattr(rs, "version_url", None)),
                )
            )
        return systems
