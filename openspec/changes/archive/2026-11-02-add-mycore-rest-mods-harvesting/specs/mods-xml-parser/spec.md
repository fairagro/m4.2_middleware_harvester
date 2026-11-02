## Purpose

Shared PayloadParser that turns a MyCoRe object XML document (or a bare MODS document) into a typed `mods_record`
payload for the `mods_general` DataMapper.

## ADDED Requirements

### Requirement: Provide a mods_xml PayloadParser

The system SHALL provide a shared PayloadParser in `middleware.parsing`, selectable by registry key `mods_xml`, whose
`produces` kind is `mods_record`. It SHALL accept a URL discovery unit, fetching the unit's fetch URL when set and its
URL otherwise through the shared polite HTTP client, and SHALL accept an inline XML discovery unit without requiring an
HTTP client.

#### Scenario: URL unit with fetch URL

- **WHEN** a URL discovery unit has url `https://host/receive/x` and fetch URL `https://host/api/v2/objects/x`
- **THEN** the parser requests only `https://host/api/v2/objects/x`

#### Scenario: Inline MODS without client

- **WHEN** an inline XML discovery unit carries a `mods:mods` document and no HTTP client is given
- **THEN** parsing succeeds without performing HTTP

#### Scenario: URL unit without client

- **WHEN** a URL discovery unit is parsed with no HTTP client
- **THEN** parsing fails with a descriptive error for that record

### Requirement: Locate the MODS element

The parser SHALL accept a document whose root is `mods:mods` (namespace `http://www.loc.gov/mods/v3`) or a MyCoRe
`mycoreobject` whose `metadata/def.modsContainer/modsContainer` holds exactly one `mods:mods` element. It SHALL record
the MyCoRe object `ID` attribute when present.

#### Scenario: MyCoRe envelope

- **WHEN** the document is a `mycoreobject` with `ID="openagrar_mods_00021925"` wrapping one `mods:mods`
- **THEN** the payload's record carries that MODS content and object id `openagrar_mods_00021925`

#### Scenario: Wrong root

- **WHEN** the document root is neither `mycoreobject` nor `mods:mods`
- **THEN** the parser raises `ParserError` naming the unexpected root

### Requirement: Parse XML safely and fail closed

The parser SHALL use the shared safe XML parsing (no entity expansion, DTD loading, or network retrieval). It MUST raise
`ParserError` when the body is empty, not well-formed, contains no `mods:mods`, or contains more than one `mods:mods`
inside the MyCoRe envelope.

#### Scenario: Malformed XML

- **WHEN** the fetched body is not well-formed XML
- **THEN** the parser raises `ParserError` for that discovery unit

#### Scenario: External entity

- **WHEN** the document declares an external entity pointing at a local file
- **THEN** parsing fails closed and no file content appears in the payload

### Requirement: Extract MODS fields into a typed record

The parser SHALL extract, without interpreting ARC semantics: titles (with `xml:lang`), abstracts (with `xml:lang`),
names (type, display form, given/family name parts, role codes, name identifiers with their `type`, affiliations),
identifiers with their `type`, `originInfo` dates (`dateIssued`, `dateCreated`, `dateModified`, with encoding),
`accessCondition` entries (type, `xlink:href`, text), `classification` entries (authority URI, value URI, text),
`genre`, `subject/topic` keywords, `language/languageTerm`, and `location/url`. Missing optional fields MUST yield empty
values, not errors. The payload identifier SHALL be the discovery unit's identifier.

#### Scenario: Person with ORCID and affiliation

- **WHEN** a `mods:name type="personal"` has given and family name parts, `nameIdentifier type="orcid"` and an
  `affiliation`
- **THEN** the record carries that person with both name parts, the ORCID value and the affiliation

#### Scenario: Record without abstract

- **WHEN** the MODS document has no `abstract`
- **THEN** parsing succeeds with an empty abstract list
