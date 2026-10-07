## ADDED Requirements

### Requirement: The dataset date MUST come from the citation, not gmd:dateStamp

`InspireMapper` MUST set Investigation and Study `SubmissionDate` from the citation `CI_Date` entries: the earliest
`publication` date, else the latest `revision` date, else the earliest `creation` date; without any of these it MUST
stay empty. `gmd:dateStamp` MUST NOT be used as a dataset date; it MUST be kept as the Investigation Comment
`Metadata Date`.

#### Scenario: BonaRes record

- **WHEN** a record has `dateStamp` 2026-08-18T12:06:54Z and a citation `publication` date 2026-05-19T16:11:37Z
- **THEN** `SubmissionDate` MUST be 2026-05-19T16:11:37Z and the `Metadata Date` Comment 2026-08-18T12:06:54Z

#### Scenario: No publication date

- **WHEN** a record has `creation` and `revision` dates only
- **THEN** `SubmissionDate` MUST be the latest `revision` date

#### Scenario: No citation date

- **WHEN** a record has no typed citation date
- **THEN** `SubmissionDate` MUST be empty
