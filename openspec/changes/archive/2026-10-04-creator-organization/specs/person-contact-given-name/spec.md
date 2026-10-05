## ADDED Requirements

### Requirement: Organisational creators MUST be the Comment `Creator Organization`

When an organisation is a creator or author of the dataset, the INSPIRE, Schema.org and Regal mappers MUST record it
through `middleware.payload.person_contacts.add_creator_organization`: one Investigation Comment named
`Creator Organization` with the organisation name per distinct name (case-insensitive), plus a Comment
`Creator Organization URL` when a URL different from the name is known. Contributor and publisher organisations keep
their existing Comment names.

#### Scenario: Organisation is creator and author

- **WHEN** a Schema.org Dataset has the Organization `IBSC` as both `creator` and `author`
- **THEN** the Investigation MUST have exactly one Comment `Creator Organization` with value `IBSC` and no Person
  contact

#### Scenario: Regal organisation label

- **WHEN** a Regal `creator` has `prefLabel` `NFDI4Health Task Force COVID-19` (no comma) and `@id`
  `https://example.org/org/nfdi4health-tf`
- **THEN** the Comments MUST be `Creator Organization: NFDI4Health Task Force COVID-19` and
  `Creator Organization URL: https://example.org/org/nfdi4health-tf`
