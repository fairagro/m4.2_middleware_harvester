# phenoroam-to-arc-mapping Specification

## Purpose

Map a typed PhenoRoam intermediate record (`PayloadKind.phenoroam_record`) to ARC Investigation / Study / Assay with
annotation tables, without inventing data-file Output entities from metadata-only harvests.

## Requirements

### Requirement: Provide a phenoroam_general DataMapper

The system SHALL provide a shared DataMapper registered as `mapper.type: phenoroam_general` that accepts
`PayloadKind.phenoroam_record` and returns one or more `HarvestedArc` values. The mapper MUST map `pr:` vocabulary
directly to ARC — it MUST NOT convert through Schema.org or RDF as an intermediate.

#### Scenario: Minimal record yields HarvestedArc

- **WHEN** a `phenoroam_record` payload with title, description, and identifier is mapped
- **THEN** mapping succeeds and yields a `HarvestedArc` whose Investigation carries that title and description

### Requirement: Resolve a stable unique identifier without requiring DOI

The mapper SHALL set Investigation.identifier from a unique `itemUUID` when present and non-empty after trim; otherwise
it SHALL use a resolvable PhenoRoam landing-page URL derived from that UUID (or the OAI identifier). The mapper MUST NOT
require a DOI for a successful map.

#### Scenario: itemUUID becomes the investigation identifier

- **WHEN** the record carries a non-empty `itemUUID`
- **THEN** Investigation.identifier is derived from that UUID (after shared identifier sanitization)

#### Scenario: Missing UUID falls back to landing URL

- **WHEN** `itemUUID` is missing or blank but an OAI / catalog id is available
- **THEN** Investigation.identifier is derived from the landing-page URL form, not left empty

### Requirement: Map Study and Investigation nesting from pr blocks

When `pr:blockStudy` / `pr:blockInvestigation` (under study parent) are present, the mapper SHALL populate ARC Study and
Investigation metadata from those titles/descriptions. An Assay SHALL exist for process/annotation tables even when no
data files are harvested.

#### Scenario: Nested study and investigation titles appear in ARC

- **WHEN** the record contains `blockStudy` and nested `blockInvestigation` with titles
- **THEN** the mapped ARC exposes corresponding Study and Investigation title information

### Requirement: Contacts use shared display-name split and given-name policy

Person contacts from `pr:blockPerson` (responsible and other contacts) MUST be split with
`middleware.payload.person_names.split_display_name` and MUST obey `person-contact-given-name` (non-empty given name or
Comment / fail-closed — same rules as INSPIRE and Schema.org). Affiliation from `itemAffiliation` MUST become
`Person.Affiliation` when a Person is emitted.

#### Scenario: Full name yields Person with given and family

- **WHEN** `itemName` is `Marion Deichmann` and affiliation is present
- **THEN** the Investigation contacts include a Person with non-empty given and family names and that affiliation

### Requirement: MUST NOT invent data-file Output entities from metadata links

The mapper MUST NOT create ISA Data File / Output entities (or equivalent fabricated file nodes) for `pr:listDatafiles`
/ `pr:itemLink` values. Remote file URLs MAY appear only as Investigation/Assay comments or annotation-table cells that
do not imply local file payloads. This aligns with not fabricating Raw/Processed Data entities from metadata-only
sources.

#### Scenario: Datafile links do not become file Outputs

- **WHEN** a record lists one or more non-empty `itemLink` download URLs
- **THEN** the mapped ARC MUST NOT contain invented data-file Output entities for those links; mapping still succeeds

### Requirement: Annotation tables carry harvestable metadata fields

The mapper SHALL represent keywords and, when present, license/rights and geographic bounding-box information via Assay
(or Investigation) annotation tables or comments suitable for metadata-only ARCs.

#### Scenario: Keywords appear as annotations or equivalent structured metadata

- **WHEN** the record contains keywords
- **THEN** those keywords are present in the mapped ARC as annotation-table values or equivalent structured fields
