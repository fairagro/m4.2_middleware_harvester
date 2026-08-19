# Linked Data Mapper

## Purpose

Define the mapping contract from a parsed Linked Data RDF graph to a
`HarvestedArc` (RO-Crate JSON-LD plus study/assay composition counts).

Vocabulary-specific implementations (e.g. `GeneralSchemaOrgMapper` for
schema.org, `RegalMapper` for Regal) register against `payload_type` and
implement this interface.

## Requirements

### Requirement: LinkedDataMapper.map_graph returns HarvestedArc

The system SHALL provide a `LinkedDataMapper` ABC whose `map_graph` method
accepts an `rdflib.Graph` and returns a `HarvestedArc`. Implementations MUST
build the value via `HarvestedArc.from_arctrl` (or equivalent) so the
orchestrator receives serialized ARC JSON plus composition counts without
re-parsing RO-Crate JSON. The mapper MUST NOT return a bare JSON string.

#### Scenario: Successful map produces HarvestedArc

- **WHEN** `map_graph` is called with a mappable graph
- **THEN** the return type is `HarvestedArc`, not `str`

### Requirement: Select mapper by payload_type

The system SHALL select mapper implementations using configured `payload_type`
values via the mapper registry (explicit, non-guessing selection).

#### Scenario: Configured payload selects the registered mapper

- **WHEN** plugin config sets a supported `payload_type`
- **THEN** `LinkedDataMapper.from_config` / registry resolution returns the
  matching concrete mapper

### Requirement: Keep mapping separate from discovery

The system SHALL keep mapping logic separate from sitemap discovery and dataset
payload extraction.

#### Scenario: Mapper does not fetch sitemaps

- **WHEN** a mapper implementation runs
- **THEN** it operates only on an already-built `rdflib.Graph` and does not
  perform sitemap discovery or HTTP dataset fetch

### Requirement: Mapping failures surface as HarvesterError

Mapping failures MUST be surfaced to the orchestrator as `HarvesterError`
(typically `RecordProcessingError`) and MUST NOT crash the whole harvest run.

#### Scenario: Unmappable graph

- **WHEN** a graph lacks valid dataset metadata for the selected mapper
- **THEN** the plugin yields a `HarvesterError` for that record and continues

### Requirement: Edge case — no runtime config outside payload selection

Mapper implementations MUST NOT depend on ad-hoc runtime config outside the
fields needed for the selected `payload_type` (e.g. Regal resource base URL via
`from_config`).

#### Scenario: Payload-scoped config only

- **WHEN** a mapper is constructed from plugin config
- **THEN** only configuration relevant to that `payload_type` influences
  mapping behaviour

### Requirement: Schema.org Organization publisher MUST become Comment not Person

`GeneralSchemaOrgMapper` MUST NOT append Schema.org `Organization` publishers
(or other Organization-typed nodes used as publisher) as Investigation Person
contacts. It MUST represent the publisher via an Investigation comment named
`Publisher` with the organization name, and MAY add a separate comment for the
publisher URL when present. Creator/author Person affiliations MUST continue to
use `Person.Affiliation` when the source provides them.

#### Scenario: OpenAgrar-like Dataset with authors and Zenodo publisher

- **WHEN** a Schema.org Dataset graph has Person creators with non-empty
  `givenName`/`familyName` and an Organization publisher named `Zenodo`
- **THEN** `map_graph` MUST return a HarvestedArc whose Investigation Contacts
  contain only those Person creators (each with non-empty given name), MUST
  include `Comment("Publisher", "Zenodo")` (or equivalent comment name/value),
  and MUST NOT include a Person contact for Zenodo

#### Scenario: Organization creator is not emitted as empty-given-name Person

- **WHEN** a Schema.org creator or contributor node is typed as Organization
- **THEN** the mapper MUST NOT append that node as a Person with empty given
  name; it MAY omit the contact or represent the organization via Investigation
  comment consistent with `person-contact-given-name`

### Requirement: Schema.org mapper MUST fail closed on invalid Person given names

After assembling contacts, `GeneralSchemaOrgMapper` MUST refuse to return a
`HarvestedArc` when any Person contact lacks a non-empty trimmed given name.
The failure MUST surface as a mapping error so the linked-data plugin yields a
record-level failure and does not upload.

#### Scenario: Literal creator without given name fails mapping

- **WHEN** the only creator is a single-token literal name that maps to
  last name only with an empty given name
- **THEN** `map_graph` MUST raise a mapping error and MUST NOT return a
  HarvestedArc

### Requirement: Schema.org Investigation identifier MUST be harvest-stable

`GeneralSchemaOrgMapper` MUST set `Investigation.identifier` from a catalog-stable value and MUST NOT use an rdflib blank-node label (`N` plus 32 hex digits, or `_:…`), MUST NOT hash or invent an identifier, and MUST NOT fall back to an 80-character title slug.

Resolution MUST follow this order:

1. DOI from `schema:identifier`: a literal whose value starts with `10.`, or a `PropertyValue` whose `propertyID` is an identifiers.org DOI URI or contains `doi` (case-insensitive) and whose `schema:value` starts with `10.` (optional `https://doi.org/` / `http://doi.org/` / `doi:` prefix MAY be stripped).
2. Otherwise a canonical `http(s)` source URL from `schema:url`, then `schema:sameAs`, then the Dataset `@id` when it is an `http(s)` IRI. The URL MUST be sanitized for arctrl identifier constraints (letters, digits, underscore, dash, space): the scheme is stripped, forbidden characters are replaced with `_`, and consecutive underscores are collapsed.
3. Otherwise the discovered dataset page URL supplied by the plugin (sanitized as above).

#### Scenario: OpenAgrar PropertyValue DOI without Dataset @id

- **WHEN** a Schema.org Dataset graph has no `@id`, `url`, or `sameAs`, and `schema:identifier` is a `PropertyValue` with `propertyID` `https://registry.identifiers.org/registry/doi` and `value` `10.3220/253-2025-42`
- **THEN** `Investigation.identifier` MUST be `10.3220/253-2025-42` and MUST NOT match an rdflib blank-node label

#### Scenario: Two parses of the same payload yield the same identifier

- **WHEN** the same Schema.org JSON-LD payload is parsed into a graph twice and mapped twice
- **THEN** both mappings MUST produce the same `Investigation.identifier`

#### Scenario: OpenAgrar record without DOI uses sanitized source URL

- **WHEN** a Schema.org Dataset graph has no DOI and no `url`/`sameAs`/`http(s)` `@id`, and the discovered page URL is `https://www.openagrar.de/receive/openagrar_mods_00107322`
- **THEN** `Investigation.identifier` MUST be `www_openagrar_de_receive_openagrar_mods_00107322`

#### Scenario: Missing DOI and missing source URL fails mapping

- **WHEN** a Schema.org Dataset graph has no DOI and no `http(s)` `url`/`sameAs`/`@id`, and no discovered page URL is supplied
- **THEN** mapping MUST raise a mapping error, MUST NOT return a `HarvestedArc`, and MUST NOT use `str(subject)` of a blank node as the identifier

### Requirement: Schema.org mapping failures without a stable identifier MUST become record-level harvest errors

When Schema.org mapping refuses a record for lack of a stable identifier, the linked-data plugin MUST yield a `RecordProcessingError` (a `HarvesterError`) for that record and MUST NOT upload an ARC. The harvest run MUST continue with remaining records.

#### Scenario: Unidentifiable Dataset is reported, not uploaded

- **WHEN** Schema.org mapping raises because no DOI, URL, or source URL is available
- **THEN** the plugin MUST yield `RecordProcessingError` for that dataset and MUST NOT yield a `HarvestedArc` for it
