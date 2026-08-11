## ADDED Requirements

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
