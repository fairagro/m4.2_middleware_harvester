## Purpose

Map a typed MODS intermediate record (`PayloadKind.mods_record`) directly to a metadata-only ARC. Authoritative field
rules live in `docs/mappers/mods.md`; this spec is the implementation contract.

## ADDED Requirements

### Requirement: Authoritative MODS mapping document

The MODS→ARC field tables SHALL live in `docs/mappers/mods.md` (`payload_kind: mods_record`, `mapper_id: mods_general`).
This spec MUST NOT restate those tables, and the implementation SHALL honour that document.

#### Scenario: Contributor looks up a MODS field

- **WHEN** a contributor needs the ARC target of a MODS element
- **THEN** they find it in `docs/mappers/mods.md`

### Requirement: Provide a mods_general DataMapper

The system SHALL register a DataMapper `mods_general` that accepts `PayloadKind.mods_record` and yields one
`HarvestedArc` per record. It MUST map MODS directly to ARC without converting through Schema.org or RDF, and MUST NOT
perform HTTP requests.

#### Scenario: Minimal record

- **WHEN** a `mods_record` with a title and a MyCoRe object id is mapped
- **THEN** one `HarvestedArc` is yielded whose Investigation carries that title

### Requirement: Keep the harvest-source identity cascade

Investigation.identifier SHALL be derived, after shared identifier sanitization, from the first non-empty of: the
discovery `harvest_source_id`, the MyCoRe object id on the record, then a DOI from `identifier type="doi"`. A DOI not
used as identifier MUST still be kept in the ARC as described in `docs/mappers/mods.md`. When none is available the
mapper MUST refuse the record (no invented identifier).

#### Scenario: Same identifier as the schema.org path

- **WHEN** an object discovered with `harvest_source_id` `openagrar_mods_00021925` is mapped by `mods_general`
- **THEN** Investigation.identifier equals the value `schema_org_general` produces today for the same discovery unit

#### Scenario: No identity available

- **WHEN** the record has no harvest source id, no object id and no DOI
- **THEN** mapping fails with a record-level error

### Requirement: Require a title without inventing one

The mapper SHALL take the Investigation title from the primary `titleInfo/title` (prefer an entry without `type`, then
the first) and MUST refuse a record without any non-empty title.

#### Scenario: Missing title

- **WHEN** the record has no non-empty title
- **THEN** mapping fails with a record-level error and no placeholder title is used

### Requirement: Contacts follow shared person policy

Personal names SHALL become ARC Persons using MODS given/family name parts when present and the shared display-name
split otherwise, and MUST obey `person-contact-given-name`. ORCID identifiers SHALL become the Person ORCID; an
affiliation SHALL become Person.Affiliation. Corporate names SHALL NOT become Persons. Their placement is defined in
`docs/mappers/mods.md`.

#### Scenario: Personal author

- **WHEN** a personal name has family `Pantiukhin`, given `Dmitrii`, ORCID `0000-0002-3427-8188` and an affiliation
- **THEN** the Investigation contacts include a Person with those names, that ORCID and that affiliation

#### Scenario: Corporate name

- **WHEN** a `mods:name type="corporate"` is present
- **THEN** no Person is created for it

### Requirement: Licence and dates use shared helpers

Licence information from `accessCondition type="use and reproduction"` and DCAT licence classifications SHALL be placed
with the shared ARC licence helper, and dates with the shared ARC date helpers, as described in `docs/mappers/mods.md`.

#### Scenario: CC BY licence

- **WHEN** the record has `accessCondition type="use and reproduction"` pointing at a CC BY 4.0 licence URI
- **THEN** the ARC carries that licence the same way the other base mappers place licences
