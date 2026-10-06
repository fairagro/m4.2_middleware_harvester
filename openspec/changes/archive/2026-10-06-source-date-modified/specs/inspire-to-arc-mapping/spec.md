## ADDED Requirements

### Requirement: The latest revision date MUST be dateModified

`InspireMapper` MUST add the Investigation Comment `dateModified` (RO-Crate root `dateModified`) from the latest
citation `CI_Date` of type `revision`. `gmd:dateStamp` MUST NOT be used; without a revision date there MUST be no
`dateModified`.

#### Scenario: Two revision dates

- **WHEN** a record has revision dates 2021-05-05 and 2023-07-07
- **THEN** the RO-Crate root `dateModified` MUST be "2023-07-07"

#### Scenario: Only a dateStamp

- **WHEN** a record has `dateStamp` 2026-08-18 and no revision date
- **THEN** the RO-Crate root MUST NOT have `dateModified`
