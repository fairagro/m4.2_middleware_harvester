## MODIFIED Requirements

### Requirement: The dataset date MUST come from the citation, not gmd:dateStamp

`InspireMapper` MUST set Investigation and Study `PublicReleaseDate` (RO-Crate `datePublished`) from the citation
`CI_Date` entries: the earliest `publication` date, else the latest `revision` date, else the earliest `creation` date;
without any of these it MUST stay empty. Investigation and Study `SubmissionDate` (RO-Crate `dateCreated`) MUST be the
earliest `creation` date, and empty without one. `gmd:dateStamp` MUST NOT be used as a dataset date; it MUST be kept as
the Investigation Comment `Metadata Date`.

#### Scenario: BonaRes record

- **WHEN** a record has `dateStamp` 2026-08-18T12:06:54Z and a citation `publication` date 2026-05-19T16:11:37Z
- **THEN** `PublicReleaseDate` MUST be 2026-05-19T16:11:37Z, `SubmissionDate` MUST be empty and the `Metadata Date`
  Comment 2026-08-18T12:06:54Z

#### Scenario: No publication date

- **WHEN** a record has `creation` and `revision` dates only
- **THEN** `PublicReleaseDate` MUST be the latest `revision` date and `SubmissionDate` the earliest `creation` date

#### Scenario: No citation date

- **WHEN** a record has no typed citation date
- **THEN** `PublicReleaseDate` and `SubmissionDate` MUST be empty
