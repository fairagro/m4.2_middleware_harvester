## ADDED Requirements

### Requirement: INSPIRE MUST map ISO contacts by individualName vs organisationName

The INSPIRE mapper MUST treat ISO `CI_ResponsibleParty` fields as typed signals: `individualName` identifies a person;
`organisationName` identifies an organization (or a person's affiliation when both are present).

1. When `individualName` is present, the mapper MUST split it with `middleware.payload.person_names.split_display_name`.
   If that split does not yield a non-empty given name (for example an org-unit acronym such as `RTH`), the mapper MUST
   NOT fail the record for that reason and MUST NOT emit a Person contact. It MUST instead emit an Investigation Comment
   named from the contact role, with value `<organisationName> (<individualName>)` when `organisationName` is present,
   else the trimmed `individualName`. This is the same Organization→Comment policy as `linked-data-mapper` ("Schema.org
   Organization publisher MUST become Comment not Person") and the Regal label-agent rule.
2. When only `organisationName` is present (no `individualName`), the mapper MUST emit an Investigation Comment named
   from the contact role (for example `Publisher`, `Point of Contact`) with the organization name, and MUST NOT emit a
   Person contact.
3. When both are present and the individualName split succeeds, the mapper MUST emit a Person with that given/family
   name and MUST set `Person.Affiliation` from `organisationName`.

Comments produced by rules 1 and 2 MUST be deduplicated by role name and value (case-insensitive).

#### Scenario: INSPIRE organisation-only contact becomes Comment

- **WHEN** a CI_ResponsibleParty has `organisationName` `Zenodo`, role `publisher`, and no `individualName`
- **THEN** the Investigation MUST include a Comment named `Publisher` with value `Zenodo` and MUST NOT append a Person
  for Zenodo

#### Scenario: INSPIRE unparseable individualName with organisation becomes Comment

- **WHEN** a CI_ResponsibleParty has `individualName` `RTH`, `organisationName` `Deutscher Wetterdienst`, and role
  `pointOfContact`
- **THEN** mapping MUST succeed, the Investigation MUST include a Comment named `Point of Contact` with value
  `Deutscher Wetterdienst (RTH)`, and MUST NOT append a Person for that contact

#### Scenario: INSPIRE unparseable individualName alone becomes Comment

- **WHEN** a CI_ResponsibleParty has `individualName` `RTH`, no `organisationName`, and role `pointOfContact`
- **THEN** mapping MUST succeed, the Investigation MUST include a Comment named `Point of Contact` with value `RTH`, and
  MUST NOT append a Person for that contact

#### Scenario: INSPIRE individual plus organisation maps Person with Affiliation

- **WHEN** a CI_ResponsibleParty has `individualName` `Jane Doe` and `organisationName` `Acme Corp`
- **THEN** the Investigation MUST contain a Person with given `Jane`, family `Doe`, and Affiliation `Acme Corp`

## REMOVED Requirements

### Requirement: INSPIRE MUST use ISO individualName vs organisationName

**Reason**: Its fail-closed rule for an `individualName` without a given name dropped whole records (DWD `RTH`, #354).
**Migration**: Superseded by "INSPIRE MUST map ISO contacts by individualName vs organisationName", which demotes such
contacts to a role Comment.

## MODIFIED Requirements

### Requirement: Display-name splitting is shared and parser-backed (Schema.org)

When the Schema.org mapper must derive given/family names from a display string (`schema:name` / literal creator) rather
than from structured given/family fields, it MUST use the shared `middleware.payload.person_names.split_display_name`
helper (backed by `nameparser`). It MUST NOT keep private whitespace/last-token split heuristics for Person contacts.
Single-token display strings MUST continue to yield no usable given name so organization-like labels remain fail-closed
or Comment-mapped. The INSPIRE mapper MUST use the same helper for `individualName` values (demote to a Comment when
given name is missing; see INSPIRE ISO field requirement above).

Regal agent `skos:prefLabel` values follow the PUBLISSO/Regal `FamilyName, Given Name(s)` convention and MUST be split
on the first `", "` as specified in `regal-to-arc-mapping` / `docs/regal_mapping.md` (not via `split_display_name`).
Labels without `", "` are organization/label agents.

#### Scenario: Particle and title-bearing display names split consistently

- **WHEN** a display name such as `Dr. Juan Q. Xavier de la Vega III` is split for a Person contact
- **THEN** the shared helper MUST produce a non-empty given name and a family name that retains particles such as
  `de la`, and MUST NOT assign the title or suffix as the family name

#### Scenario: Single-token label has no given name

- **WHEN** the only display string is a single token such as `Zenodo`
- **THEN** `split_display_name` MUST return an empty/missing given name so the mapper can fail closed or emit an
  Organization Comment per existing rules
