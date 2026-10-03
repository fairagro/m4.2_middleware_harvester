## ADDED Requirements

### Requirement: One contact per person across creator, author and contributor

`GeneralSchemaOrgMapper` MUST add every `creator`, `author` and `contributor` Person via
`add_contact(..., match_name=True)`. A Person that has the same ORCID as an existing contact, or else the same given and
family name (case-insensitive) while not both carry different ORCIDs, MUST add its role to that contact instead of
creating another.

#### Scenario: e!DAL author array repeats contributors

- **WHEN** a Dataset has 5 `creator`s, 8 `author`s (the 5 creators plus 3 contributors) and the 3 `contributor`s
- **THEN** the Investigation MUST have 8 contacts: the 5 creators with role author and the 3 contributors with roles
  author and contributor

#### Scenario: Contributor only

- **WHEN** a Person is only a `contributor`
- **THEN** its contact MUST have only the role contributor

#### Scenario: Same name, different ORCIDs

- **WHEN** two Persons share given and family name but have different ORCIDs
- **THEN** they MUST stay two contacts
