"""Domain models for INSPIRE metadata records.

These Pydantic models represent ISO 19139-derived structures consumed by the
shared ``inspire_general`` DataMapper. Protocol plugins (CSW IsoParser, future
OAI+ISO) produce ``InspireRecord`` instances; they do not live in protocol
packages.

Every value comes from a remote server and is untrusted, so the models validate it:
length and list-size limits (``ValueBounds``, exposed by protocol configs such as the
INSPIRE plugin's ``Config.value_bounds``), a URL-scheme allowlist, ISO 19139 codelists
and ISO 639-2 language codes. A violation raises ``ValidationError`` — values are never
truncated or dropped — and the record is reported as failed.

The configured limits reach the validators through the validation context
(``InspireRecord.model_validate(data, context={VALUE_BOUNDS_CONTEXT_KEY: bounds})``).
Nested models only see that context when validated from dicts, so parsers must pass
nested entries as dicts. Without a context (direct construction in tests), the
``ValueBounds`` defaults apply.
"""

import re
from collections.abc import Callable, Sized
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field, StringConstraints, ValidationInfo

from middleware.payload.inspire.value_bounds import ValueBounds

VALUE_BOUNDS_CONTEXT_KEY = "value_bounds"

_DEFAULT_BOUNDS = ValueBounds()


def _bounds(info: ValidationInfo) -> ValueBounds:
    if isinstance(info.context, dict):
        bounds = info.context.get(VALUE_BOUNDS_CONTEXT_KEY)
        if isinstance(bounds, ValueBounds):
            return bounds
    return _DEFAULT_BOUNDS


def _max_len(limit: str) -> Callable[[str, ValidationInfo], str]:
    def check(value: str, info: ValidationInfo) -> str:
        max_len: int = getattr(_bounds(info), limit)
        if len(value) > max_len:
            # The value itself is not echoed: it may be huge and ends up in the harvest report.
            raise ValueError(f"string of length {len(value)} exceeds value_bounds.{limit}={max_len}")
        return value

    return check


def _check_max_items(value: object, info: ValidationInfo) -> object:
    # BeforeValidator: reject an oversized list before validating each of its items.
    max_items = _bounds(info).max_list_items
    if isinstance(value, Sized) and not isinstance(value, str) and len(value) > max_items:
        raise ValueError(f"list of {len(value)} items exceeds value_bounds.max_list_items={max_items}")
    return value


def _check_url(value: str, info: ValidationInfo) -> str:
    bounds = _bounds(info)
    if len(value) > bounds.max_str_medium:
        raise ValueError(f"URL of length {len(value)} exceeds value_bounds.max_str_medium={bounds.max_str_medium}")
    try:
        parsed = urlsplit(value)
    except ValueError as e:
        raise ValueError("malformed URL") from e
    scheme = parsed.scheme.lower()
    if scheme not in bounds.allowed_url_schemes:
        allowed = ", ".join(sorted(bounds.allowed_url_schemes))
        raise ValueError(f"URL scheme {scheme or '<none>'!r} not in value_bounds.allowed_url_schemes ({allowed})")
    if not parsed.netloc:
        raise ValueError("URL has no host")
    return value


def _blank_to_none(value: object) -> object:
    # OWSLib reports an absent gmx:Anchor href as "" — that is "no URL", not a bad URL.
    if isinstance(value, str) and not value.strip():
        return None
    return value


ShortStr = Annotated[str, AfterValidator(_max_len("max_str_short"))]
MediumStr = Annotated[str, AfterValidator(_max_len("max_str_medium"))]
LongStr = Annotated[str, AfterValidator(_max_len("max_str_long"))]
RequiredMediumStr = Annotated[str, StringConstraints(min_length=1), AfterValidator(_max_len("max_str_medium"))]
RequiredLongStr = Annotated[str, StringConstraints(min_length=1), AfterValidator(_max_len("max_str_long"))]
HarvestedUrl = Annotated[str, StringConstraints(strip_whitespace=True), AfterValidator(_check_url)]
OptionalUrl = Annotated[HarvestedUrl | None, BeforeValidator(_blank_to_none)]

_URN = re.compile(r"^urn:[a-z0-9][a-z0-9-]{0,31}:\S+$", re.IGNORECASE)


def _check_uri(value: str, info: ValidationInfo) -> str:
    # gmd:dataSetURI is a URI, not necessarily a URL: URNs are legitimate there.
    if _URN.match(value):
        return _max_len("max_str_medium")(value, info)
    return _check_url(value, info)


OptionalUri = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True), AfterValidator(_check_uri)] | None,
    BeforeValidator(_blank_to_none),
]
MaxItems = BeforeValidator(_check_max_items)

# ISO 639-2 three-letter language code (INSPIRE mandates ISO 639-2/B, e.g. "ger", "eng").
LanguageCode = Annotated[str, StringConstraints(pattern=r"^[a-z]{3}$")]

# ISO 8601 date or date-time as found in gco:Date / gco:DateTime.
IsoDate = Annotated[
    str,
    # Fractional seconds capped at 9 digits (ns) so the pattern itself bounds the length.
    StringConstraints(pattern=r"^\d{4}(-\d{2}(-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,9})?)?(Z|[+-]\d{2}:?\d{2})?)?)?)?$"),
]

# Deliberately loose: one "@", no whitespace. Deliverability is not our concern.
Email = Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+$"), AfterValidator(_max_len("max_str_medium"))]

# ISO 19139 codelists (gmxCodelists.xml), including the ISO 19115-1 additions so
# catalogues on the newer standard are not rejected.
CharacterSetCode = Literal[
    "ucs2", "ucs4", "utf7", "utf8", "utf16",
    "8859part1", "8859part2", "8859part3", "8859part4", "8859part5", "8859part6", "8859part7",
    "8859part8", "8859part9", "8859part10", "8859part11", "8859part13", "8859part14", "8859part15",
    "8859part16", "jis", "shiftJIS", "eucJP", "usAscii", "ebcdic", "eucKR", "big5", "GB2312",
]  # fmt: skip
ScopeCode = Literal[
    "attribute", "attributeType", "collectionHardware", "collectionSession", "dataset", "series",
    "nonGeographicDataset", "dimensionGroup", "feature", "featureType", "propertyType", "fieldSession",
    "software", "service", "model", "tile",
    # ISO 19115-1
    "metadata", "initiative", "sample", "document", "repository", "aggregate", "product", "collection",
    "coverage", "application", "sensor", "sensorSeries", "platformSeries", "productionSeries",
    "transferAggregate", "otherAggregate", "stereomate",
]  # fmt: skip
ProgressCode = Literal[
    "completed", "historicalArchive", "obsolete", "onGoing", "planned", "required", "underDevelopment",
    # ISO 19115-1
    "final", "pending", "retired", "superseded", "tentative", "valid", "accepted", "notAccepted",
    "withdrawn", "proposed", "deprecated",
]  # fmt: skip
RoleCode = Literal[
    "resourceProvider", "custodian", "owner", "user", "distributor", "originator", "pointOfContact",
    "principalInvestigator", "processor", "publisher", "author",
    # ISO 19115-1
    "sponsor", "coAuthor", "collaborator", "editor", "mediator", "rightsHolder", "contributor", "funder",
    "stakeholder",
]  # fmt: skip
DateTypeCode = Literal[
    "creation", "publication", "revision",
    # ISO 19115-1
    "expiry", "lastUpdate", "lastRevision", "nextUpdate", "unavailable", "inForce", "adopted",
    "deprecated", "superseded", "validityBegins", "validityExpires", "released", "distribution",
]  # fmt: skip
TopicCategoryCode = Literal[
    "farming", "biota", "boundaries", "climatologyMeteorologyAtmosphere", "economy", "elevation",
    "environment", "geoscientificInformation", "health", "imageryBaseMapsEarthCover",
    "intelligenceMilitary", "inlandWaters", "location", "oceans", "planningCadastre", "society",
    "structure", "transportation", "utilitiesCommunication",
    # ISO 19115-1
    "extraTerrestrial", "disaster",
]  # fmt: skip
# gco:Boolean lexical space (xs:boolean).
BooleanLiteral = Literal["true", "false", "1", "0"]


class ResourceIdentifier(BaseModel):
    """Resource identifier (DOI, ISBN, etc.)."""

    code: RequiredMediumStr
    codespace: MediumStr | None = None
    url: OptionalUrl = None


class InspireDate(BaseModel):
    """Date with type (creation, publication, revision)."""

    date: IsoDate
    datetype: DateTypeCode | None = None


class SpatialResolutionDistance(BaseModel):
    """Spatial resolution as distance with unit."""

    value: float
    uom: ShortStr  # Unit of measure (e.g., "m", "km")


class DistributionFormat(BaseModel):
    """Data distribution format information."""

    name: RequiredMediumStr
    version: ShortStr | None = None
    specification: MediumStr | None = None
    name_url: OptionalUrl = None
    version_url: OptionalUrl = None
    specification_url: OptionalUrl = None


class OnlineResource(BaseModel):
    """Online resource (download link, service endpoint, etc.)."""

    url: HarvestedUrl
    protocol: ShortStr | None = None
    protocol_url: OptionalUrl = None
    name: MediumStr | None = None
    name_url: OptionalUrl = None
    description: LongStr | None = None
    description_url: OptionalUrl = None
    function: ShortStr | None = None  # "download", "information", etc.


class ConformanceResult(BaseModel):
    """Data quality conformance result."""

    specification_title: RequiredMediumStr
    specification_title_url: OptionalUrl = None
    specification_date: IsoDate | None = None
    specification_datetype: DateTypeCode | None = None
    degree: BooleanLiteral | None = None


class ReferenceSystem(BaseModel):
    """Coordinate reference system information."""

    code: RequiredMediumStr
    code_url: OptionalUrl = None
    codespace: MediumStr | None = None
    codespace_url: OptionalUrl = None
    version: ShortStr | None = None
    version_url: OptionalUrl = None


class Contact(BaseModel):
    """Enhanced contact information with full CI_ResponsibleParty details."""

    # Core fields (existing)
    name: MediumStr | None = None
    name_url: OptionalUrl = None
    organization: MediumStr | None = None
    organization_url: OptionalUrl = None
    email: Email | None = None
    role: RoleCode | None = None
    type: Literal["metadata", "resource"] | None = None

    # Extended fields (new)
    position: MediumStr | None = None
    phone: ShortStr | None = None
    fax: ShortStr | None = None
    address: MediumStr | None = None
    city: MediumStr | None = None
    region: MediumStr | None = None
    postcode: ShortStr | None = None
    country: MediumStr | None = None
    online_resource_url: OptionalUrl = None
    online_resource_protocol: ShortStr | None = None
    online_resource_name: MediumStr | None = None
    online_resource_description: LongStr | None = None


class InspireRecord(BaseModel):
    """Comprehensive representation of an INSPIRE metadata record."""

    # Core identification (existing fields)
    identifier: RequiredMediumStr
    title: RequiredMediumStr
    abstract: RequiredLongStr
    date_stamp: IsoDate | None = None
    keywords: Annotated[list[MediumStr], MaxItems, Field(default_factory=list)]
    topic_categories: Annotated[list[TopicCategoryCode], MaxItems, Field(default_factory=list)]
    contacts: Annotated[list[Contact], MaxItems, Field(default_factory=list)]
    lineage: LongStr | None = None
    spatial_extent: Annotated[list[float], Field(min_length=4, max_length=4)] | None = None  # [minx, miny, maxx, maxy]
    temporal_extent: tuple[ShortStr | None, ShortStr | None] | None = None  # (start, end)
    constraints: Annotated[list[MediumStr], MaxItems, Field(default_factory=list)]

    # Metadata-level fields (new)
    parent_identifier: MediumStr | None = None
    language: LanguageCode | None = None
    charset: CharacterSetCode | None = None
    hierarchy: ScopeCode | None = None
    metadata_standard_name: MediumStr | None = None
    metadata_standard_version: ShortStr | None = None
    dataset_uri: OptionalUri = None

    # Identification - Core (new)
    alternate_title: MediumStr | None = None
    resource_identifiers: Annotated[list[ResourceIdentifier], MaxItems, Field(default_factory=list)]
    edition: ShortStr | None = None
    purpose: LongStr | None = None
    status: ProgressCode | None = None
    resource_language: Annotated[list[LanguageCode], MaxItems, Field(default_factory=list)]
    graphic_overviews: Annotated[list[HarvestedUrl], MaxItems, Field(default_factory=list)]  # thumbnail URLs

    # Identification - Dates (new)
    dates: Annotated[list[InspireDate], MaxItems, Field(default_factory=list)]

    # Identification - Resolution (new)
    spatial_resolution_denominators: Annotated[list[int], MaxItems, Field(default_factory=list)]
    spatial_resolution_distances: Annotated[list[SpatialResolutionDistance], MaxItems, Field(default_factory=list)]

    # Identification - Contacts by role (new)
    creators: Annotated[list[Contact], MaxItems, Field(default_factory=list)]  # role=originator
    publishers: Annotated[list[Contact], MaxItems, Field(default_factory=list)]  # role=publisher
    contributors: Annotated[list[Contact], MaxItems, Field(default_factory=list)]  # role=author

    # Constraints (detailed, new)
    access_constraints: Annotated[list[MediumStr], MaxItems, Field(default_factory=list)]
    use_constraints: Annotated[list[MediumStr], MaxItems, Field(default_factory=list)]
    classification: Annotated[list[MediumStr], MaxItems, Field(default_factory=list)]
    other_constraints: Annotated[list[MediumStr], MaxItems, Field(default_factory=list)]
    other_constraints_url: Annotated[list[HarvestedUrl], MaxItems, Field(default_factory=list)]

    # Distribution (new)
    distribution_formats: Annotated[list[DistributionFormat], MaxItems, Field(default_factory=list)]
    online_resources: Annotated[list[OnlineResource], MaxItems, Field(default_factory=list)]

    # Data Quality (new)
    conformance_results: Annotated[list[ConformanceResult], MaxItems, Field(default_factory=list)]
    lineage_url: OptionalUrl = None  # if lineage uses gmx:Anchor

    # Reference System (new)
    reference_systems: Annotated[list[ReferenceSystem], MaxItems, Field(default_factory=list)]

    # Supplemental (new)
    supplemental_information: LongStr | None = None

    # Note: acquisition and contentinfo are complex nested objects that will be
    # handled separately if needed (mapped as Assay Protocols in the mapper)
