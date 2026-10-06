## ADDED Requirements

### Requirement: Source dateModified MUST reach the RO-Crate root

`GeneralSchemaOrgMapper` MUST add the Investigation Comment `dateModified` (ARCtrl writes it as the RO-Crate root
`dateModified`) from `schema:dateModified`, normalised by `middleware.payload.iso_dates.iso_date`. A value that is not a
date MUST NOT produce the Comment. The harvest time MUST NOT be used.

#### Scenario: Dataset with dateModified

- **WHEN** a Dataset has `dateModified` "2019-03-04"
- **THEN** the RO-Crate root `dateModified` MUST be "2019-03-04"

#### Scenario: No dateModified

- **WHEN** a Dataset has no `dateModified`
- **THEN** the RO-Crate root MUST NOT have `dateModified`
