# mods-to-arc-mapping Specification

## Purpose

Map intermediate `mods_record` payloads to ARC. Authoritative field tables live in `docs/mappers/mods.md`; this spec
defines the mapper contract and coverage bar for the OpenAgrar cutover.

## Requirements

### Requirement: Provide mods_general DataMapper

The system SHALL register mapper type `mods_general` as a `DataMapper` that accepts `PayloadKind.mods_record`, lives in
`middleware.payload`, and maps each record to ARC per `docs/mappers/mods.md`. The mapper MUST NOT perform MyCoRe
discovery or HTTP fetches.

#### Scenario: mods_general accepts mods_record

- **WHEN** mapper type `mods_general` is selected
- **THEN** the implementation accepts `PayloadKind.mods_record` and returns `HarvestedArc` value(s) for a mappable
  record

#### Scenario: Mapper does not call MyCoRe APIs

- **WHEN** `mods_general` runs
- **THEN** it operates only on an already-built `mods_record` payload

### Requirement: Cover OpenAgrar parity fields

For OpenAgrar-class MODS research-data records, `mods_general` SHALL map at least: title, abstract/description, creators
(with optional GND/ORCID identifiers and affiliation when present), DOI identifier, licence / use-and- reproduction URI,
and publication / issued date — sufficient to meet or exceed the ARC coverage previously obtained via
`schema_org_general` on OpenAgrar HTML JSON-LD for the same objects, plus DOI and licence when present in MODS.
`Investigation.Identifier` SHALL prefer the MyCoRe object id (`harvest_source_id` / record object id) over the DOI so
existing OpenAgrar ARCs are updated in place.

#### Scenario: DOI and licence surface when present in MODS

- **WHEN** MODS contains a DOI identifier and an accessCondition / licence URI
- **THEN** the harvested ARC includes corresponding publication DOI and licence information per `docs/mappers/mods.md`

#### Scenario: Object id wins over DOI for Investigation.Identifier

- **WHEN** both a MyCoRe object id and a DOI are available
- **THEN** `Investigation.Identifier` is derived from the object id (not the DOI)

### Requirement: Authoritative mapping doc

The system SHALL publish `docs/mappers/mods.md` as the authoritative MODS→ARC field contract. Feature specs MUST link to
it and MUST NOT duplicate full field tables.

#### Scenario: Spec links to docs/mappers/mods.md

- **WHEN** this capability cites field placement rules
- **THEN** it references `docs/mappers/mods.md` rather than copying the full table
