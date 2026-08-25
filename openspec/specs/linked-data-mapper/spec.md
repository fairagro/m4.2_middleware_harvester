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

`GeneralSchemaOrgMapper` MUST set `Investigation.identifier` from a harvest-stable value and MUST NOT use an rdflib blank-node label (`N` plus 32 hex digits, or `_:…`), MUST NOT hash or invent an identifier, and MUST NOT fall back to an 80-character title slug.

Resolution MUST follow this decision chain:

1. When `harvest_source_id` is supplied (from the sitemap/discovery layer), `Investigation.identifier` MUST be that value. DOI(s) from the graph MUST NOT be used as `Investigation.identifier` when step 1 applies.
2. Else when the plugin supplies a discovered page URL (`source_url`), `Investigation.identifier` MUST be the sanitized discovered page URL. DOI(s) from the graph MUST NOT be used as `Investigation.identifier` when step 2 applies.
3. Else when the graph provides a canonical `http(s)` source URL via `schema:url`, then `schema:sameAs`, then the Dataset `@id` when it is an `http(s)` IRI, `Investigation.identifier` MUST be that URL sanitized for arctrl identifier constraints.
4. Else if exactly one valid DOI is present, `Investigation.identifier` MAY be that DOI (last resort for isolated graphs without harvest context).
5. Else if multiple valid DOIs are present without harvest or graph URL context, `Investigation.identifier` MUST be the lexicographic minimum of the normalized DOI strings (Unicode `casefold` comparison). Non-canonical DOIs MUST appear as Investigation Comments named `Alternate Identifier`.
6. Else mapping MUST fail closed (mapping error; no `HarvestedArc`).

When `harvest_source_id` or `source_url` is supplied and the graph lists multiple DOIs, non-canonical DOIs MUST appear as Investigation Comments named `Alternate Identifier`. The canonical Publication DOI MUST be the lexicographic minimum regardless of rdflib or JSON-LD order.

DOI extraction rules are unchanged: a literal whose value starts with `10.`, or a `PropertyValue` whose `propertyID` is an identifiers.org DOI URI or contains `doi` (case-insensitive) and whose `schema:value` starts with `10.`.

#### Scenario: OpenAgrar PropertyValue DOI with harvest source id uses catalog id

- **WHEN** a Schema.org Dataset graph has `schema:identifier` as a `PropertyValue` with DOI `10.3220/253-2025-42`, the discovered page URL is `https://www.openagrar.de/receive/openagrar_mods_00107322`, and `harvest_source_id` is `openagrar_mods_00107322`
- **THEN** `Investigation.identifier` MUST be `openagrar_mods_00107322` and the DOI MUST appear in ARC metadata but MUST NOT be `Investigation.identifier`

#### Scenario: OpenAgrar PropertyValue DOI without source URL falls back to DOI

- **WHEN** a Schema.org Dataset graph has no `@id`, `url`, or `sameAs`, and `schema:identifier` is a `PropertyValue` with DOI `10.3220/253-2025-42`, and no discovered page URL or `harvest_source_id` is supplied
- **THEN** `Investigation.identifier` MUST be `10.3220/253-2025-42`

#### Scenario: Two parses of the same payload yield the same identifier

- **WHEN** the same Schema.org JSON-LD payload is parsed into a graph twice and mapped twice
- **THEN** both mappings MUST produce the same `Investigation.identifier`

#### Scenario: OpenAgrar record without DOI uses sanitized source URL when no harvest source id

- **WHEN** a Schema.org Dataset graph has no DOI and no `url`/`sameAs`/`http(s)` `@id`, the discovered page URL is `https://www.openagrar.de/receive/openagrar_mods_00107322`, and no `harvest_source_id` is supplied
- **THEN** `Investigation.identifier` MUST be `www_openagrar_de_receive_openagrar_mods_00107322`

#### Scenario: OpenAgrar record without DOI uses harvest source id when supplied

- **WHEN** the same graph and page URL as above, and `harvest_source_id` is `openagrar_mods_00107322`
- **THEN** `Investigation.identifier` MUST be `openagrar_mods_00107322`

#### Scenario: Multiple DOIs with harvest source id preserve alternates

- **WHEN** a Schema.org Dataset has DOIs `10.5281/zenodo.15672440` and `10.3220/253-2025-54` in either order, `source_url` is `https://www.openagrar.de/receive/openagrar_mods_00107508`, and `harvest_source_id` is `openagrar_mods_00107508`
- **THEN** `Investigation.identifier` MUST be `openagrar_mods_00107508` on every mapping and the mapped ARC MUST contain an Investigation Comment named `Alternate Identifier` with the non-canonical DOI

#### Scenario: Shared DOI on two pages uses distinct harvest identifiers

- **WHEN** two Schema.org Dataset graphs from different Receive-URLs both contain DOI `10.1594/PANGAEA.957630`, with `harvest_source_id` values `openagrar_mods_00088718` and `openagrar_mods_00109919`
- **THEN** the mappings MUST set `Investigation.identifier` to those harvest source ids respectively and MUST NOT use the shared DOI as `Investigation.identifier`

#### Scenario: Generic source URL without harvest source id uses sanitized page URL

- **WHEN** a Schema.org Dataset graph contains DOI `10.1594/PANGAEA.957630` and `source_url` is `https://example.org/generic-page` with no `harvest_source_id`
- **THEN** `Investigation.identifier` MUST be the sanitized page URL and MUST NOT be `10.1594/PANGAEA.957630`

#### Scenario: Missing DOI and missing source URL fails mapping

- **WHEN** a Schema.org Dataset graph has no DOI and no `http(s)` `url`/`sameAs`/`@id`, and no discovered page URL is supplied
- **THEN** mapping MUST raise a mapping error, MUST NOT return a `HarvestedArc`, and MUST NOT use `str(subject)` of a blank node as the identifier

### Requirement: Schema.org mapping failures without a stable identifier MUST become record-level harvest errors

When Schema.org mapping refuses a record for lack of a stable identifier, the linked-data plugin MUST yield a `RecordProcessingError` (a `HarvesterError`) for that record and MUST NOT upload an ARC. The harvest run MUST continue with remaining records.

#### Scenario: Unidentifiable Dataset is reported, not uploaded

- **WHEN** Schema.org mapping raises because no DOI, URL, or source URL is available
- **THEN** the plugin MUST yield `RecordProcessingError` for that dataset and MUST NOT yield a `HarvestedArc` for it

### Requirement: Schema.org mapping MUST be harvest-deterministic for keywords, multi-literals, and contacts

`GeneralSchemaOrgMapper` MUST produce identical Investigation keyword comments / keyword protocol values, description text, Contact order, and Publication author strings when the logical RDF payload is unchanged — including when rdflib object iteration order differs between parses. The mapper MUST NOT rely on `graph.value` or unsorted `graph.objects` for these fields when multiple values exist.

Keyword literals MUST be trimmed and sorted with a documented stable Unicode policy before joining. When multiple Literals exist for a string predicate (at least `description`; preferably also `name` / other `_str` call sites), selection MUST drop empty values and prefer language tags in order `en`, then `de`, then untagged / other, with deterministic length-then-lexicographic tie-breaks. Creator, author, and contributor nodes MUST be sorted by a stable key (family name, given name, display name, node IRI) before Contacts are appended.

Publication author strings built from those Contacts MUST use the form `F. Last` (given-name initial, space, family name) joined with `"; "`, and MUST NOT use comma-separated `Last, F.` forms that ARCtrl splits into unstable `#Author_*` nodes.

#### Scenario: Same keywords, different RDF object order

- **WHEN** a Schema.org Dataset has the same keyword literal set presented in two different object orders
- **THEN** both mappings MUST produce the same Keywords comment text, the same joined keyword protocol value, and the same derived Keywords Comment / ParameterValue `@id`s

#### Scenario: Multi-language description with empty literal

- **WHEN** a Dataset has an empty description literal plus language-tagged `en` and `de` descriptions
- **THEN** mapping MUST select the same non-empty description on every run (preferring `en` over `de`)

#### Scenario: Same creators, different triple order

- **WHEN** the same creator/author set is present in different `graph.objects` iteration orders
- **THEN** Contact order and the Publication authors string MUST be identical across mappings

#### Scenario: Publication authors use initial-space-last form without commas

- **WHEN** a Dataset has creators Ada Lovelace and Zed Zebra (after stable Contact sort)
- **THEN** the Publication authors string / derived `#Author_*` `@id` MUST be `A. Lovelace; Z. Zebra` (or an `@id` containing that string) and MUST NOT contain a `Last, F.` comma form

#### Scenario: Double map of the same fixture graph

- **WHEN** the same Schema.org fixture graph is mapped twice
- **THEN** description, Keywords comments, Contact order, and Publication authors MUST match between the two results
