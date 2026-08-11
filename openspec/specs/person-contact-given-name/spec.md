# Person Contact Given Name

## Purpose

Defines normative rules so ARC Person contacts always carry a non-empty given
name, Organizations are never faked as empty-given-name Persons, and mapping
fails closed instead of producing ARCs that break DataHUB `arc-export`.

## Requirements

### Requirement: Person contacts MUST have a non-empty given name

Every Person contact produced by linked-data mappers (Schema.org and Regal)
MUST have a given name that is non-empty after trimming whitespace. Missing,
null, and empty-string given names MUST be treated as invalid. The system MUST
NOT invent placeholder given names such as `.`, `n/a`, or the organization name.

#### Scenario: Person with givenName maps successfully

- **WHEN** a source Person has a non-empty `givenName` (or equivalent split that
  yields a non-empty given name) and a family name
- **THEN** the mapper MUST emit a Person contact with that trimmed given name

#### Scenario: Person without given name is invalid

- **WHEN** a mapped Person contact would have a missing, null, or whitespace-only
  given name
- **THEN** the mapping MUST fail for that record (see fail-closed requirement);
  the system MUST NOT upload an ARC containing that contact

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
