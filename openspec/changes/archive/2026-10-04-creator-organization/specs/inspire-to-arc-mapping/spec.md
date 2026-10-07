## ADDED Requirements

### Requirement: Organisation-only creators MUST use `Creator Organization`

An organisation-only `CI_ResponsibleParty` (or an individualName without a given name) whose role is `author`,
`originator` or `principalInvestigator` MUST become the Investigation Comment `Creator Organization` (see
`person-contact-given-name`). Other roles MUST keep the Comment named after the role.

#### Scenario: Thünen Atlas

- **WHEN** a record's only contacts are the organisation `Thünen-Institut Zentrum für Informationsmanagement` as
  originator, author and pointOfContact
- **THEN** the Investigation MUST have one Comment `Creator Organization` and one Comment `Point of Contact` for it, and
  no Person contact

#### Scenario: Owner is not a creator

- **WHEN** an organisation-only contact has role `owner`
- **THEN** it MUST be the Comment `Owner`, not `Creator Organization`
