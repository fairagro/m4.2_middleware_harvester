# Person Contact Given Name

## Purpose

Defines normative rules so ARC Person contacts always carry a non-empty given
name, Organizations are never faked as empty-given-name Persons, and mapping
fails closed instead of producing ARCs that break DataHUB `arc-export`.

## Requirements

### Requirement: Person contacts MUST have a non-empty given name

Every Person contact produced by linked-data mappers (Schema.org and Regal)
and by the INSPIRE mapper MUST have a given name that is non-empty after
trimming whitespace. Missing, null, and empty-string given names MUST be
treated as invalid. The system MUST NOT invent placeholder given names such as
`.`, `n/a`, or the organization name.

#### Scenario: Person with givenName maps successfully

- **WHEN** a source Person has a non-empty `givenName` (or equivalent split that
  yields a non-empty given name) and a family name
- **THEN** the mapper MUST emit a Person contact with that trimmed given name

#### Scenario: Person without given name is invalid

- **WHEN** a mapped Person contact would have a missing, null, or whitespace-only
  given name
- **THEN** the mapping MUST fail for that record (see fail-closed requirement);
  the system MUST NOT upload an ARC containing that contact

### Requirement: INSPIRE MUST use ISO individualName vs organisationName

The INSPIRE mapper MUST treat ISO `CI_ResponsibleParty` fields as typed
signals: `individualName` identifies a person; `organisationName` identifies an
organization (or a person's affiliation when both are present).

1. When `individualName` is present, the mapper MUST split it with
   `middleware.harvester.person_names.split_display_name`. If that split does
   not yield a non-empty given name, mapping MUST fail closed for the record.
2. When only `organisationName` is present (no `individualName`), the mapper
   MUST emit an Investigation Comment named from the contact role (for example
   `Publisher`, `Point of Contact`) with the organization name, and MUST NOT
   emit a Person contact.
3. When both are present and the individualName split succeeds, the mapper MUST
   emit a Person with that given/family name and MUST set
   `Person.Affiliation` from `organisationName`.

#### Scenario: INSPIRE organisation-only contact becomes Comment

- **WHEN** a CI_ResponsibleParty has `organisationName` `Zenodo`, role
  `publisher`, and no `individualName`
- **THEN** the Investigation MUST include a Comment named `Publisher` with
  value `Zenodo` and MUST NOT append a Person for Zenodo

#### Scenario: INSPIRE individualName without given name fails closed

- **WHEN** a CI_ResponsibleParty has `individualName` `Jane` (no usable given
  name after split)
- **THEN** mapping MUST raise a mapping error and MUST NOT return an ARC for
  that record

#### Scenario: INSPIRE individual plus organisation maps Person with Affiliation

- **WHEN** a CI_ResponsibleParty has `individualName` `Jane Doe` and
  `organisationName` `Acme Corp`
- **THEN** the Investigation MUST contain a Person with given `Jane`, family
  `Doe`, and Affiliation `Acme Corp`

### Requirement: Organizations MUST NOT be mapped as Person with empty given name

Organization nodes (Schema.org `Organization`, Regal institution/org-style
agents that are not persons with a parseable given name) MUST NOT be appended
as Investigation contacts with an empty or missing given name.

#### Scenario: Organization publisher is not a Person contact

- **WHEN** the source has a publisher (or equivalent) typed as Organization
  with a name such as `Zenodo`
- **THEN** the Investigation Contacts list MUST NOT contain a Person whose
  last name is that organization name and whose given name is empty or missing

### Requirement: Organizations MUST be represented as Comment and/or Affiliation

Organizations MUST be represented using one or both of:

1. An Investigation comment, for example `Comment("Publisher", "<org name>")`,
   with an optional separate comment for the organization URL when present; and/or
2. `Person.Affiliation` when the organization is the affiliation of a Person in
   the source.

The system MUST NOT invent an Organization contact type or map the organization
as a Person with an empty or placeholder given name.

#### Scenario: Publisher becomes Investigation Comment

- **WHEN** a Schema.org Dataset has `publisher` as Organization named `Zenodo`
- **THEN** the Investigation MUST include a comment named `Publisher` with value
  `Zenodo` (URL MAY be a separate comment) and MUST NOT add Zenodo as a Person
  contact

#### Scenario: Creator affiliation remains Affiliation

- **WHEN** a Person creator has an organization affiliation in the source
- **THEN** that organization MUST remain on the Person as Affiliation and MUST
  NOT be converted into a separate Person contact solely to represent the org

### Requirement: Mapping MUST fail closed when any Person lacks a given name

If after mapping any Investigation Person contact would lack a non-empty
trimmed given name, the system MUST treat the record as a mapping failure:
surface a record-level error so the harvest report counts the dataset as failed,
and MUST NOT yield/upload a `HarvestedArc` for that record.

#### Scenario: Author without given name fails without upload

- **WHEN** a record's only author is a Person (or literal/label) that cannot
  yield a non-empty given name
- **THEN** mapping MUST raise/yield a record processing failure, no ARC MUST be
  uploaded for that record, and the harvest report MUST count it as failed

#### Scenario: Authors plus Organization publisher succeed

- **WHEN** a record has Person creators with non-empty given names and an
  Organization publisher
- **THEN** mapping MUST succeed with Person contacts only for those creators,
  the publisher MUST appear as a Comment (not a Person), and subsequent arctrl
  Write/load/`ToROCrateJsonString` (or equivalent round-trip used in tests)
  MUST NOT fail with `Person must have a given name`

### Requirement: Display-name splitting is shared and parser-backed (Schema.org)

When the Schema.org mapper must derive given/family names from a display string
(`schema:name` / literal creator) rather than from structured given/family
fields, it MUST use the shared
`middleware.harvester.person_names.split_display_name` helper (backed by
`nameparser`). It MUST NOT keep private whitespace/last-token split heuristics
for Person contacts. Single-token display strings MUST continue to yield no
usable given name so organization-like labels remain fail-closed or
Comment-mapped. The INSPIRE mapper MUST use the same helper for
`individualName` values (fail closed when given name is missing; see INSPIRE
ISO field requirement above).

Regal agent `skos:prefLabel` values follow the PUBLISSO/Regal
`FamilyName, Given Name(s)` convention and MUST be split on the first `", "` as
specified in `regal-to-arc-mapping` / `docs/regal_mapping.md` (not via
`split_display_name`). Labels without `", "` are organization/label agents.

#### Scenario: Particle and title-bearing display names split consistently

- **WHEN** a display name such as `Dr. Juan Q. Xavier de la Vega III` is split
  for a Person contact
- **THEN** the shared helper MUST produce a non-empty given name and a family
  name that retains particles such as `de la`, and MUST NOT assign the title or
  suffix as the family name

#### Scenario: Single-token label has no given name

- **WHEN** the only display string is a single token such as `Zenodo`
- **THEN** `split_display_name` MUST return an empty/missing given name so the
  mapper can fail closed or emit an Organization Comment per existing rules
