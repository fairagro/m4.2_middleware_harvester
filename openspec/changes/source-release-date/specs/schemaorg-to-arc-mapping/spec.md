## MODIFIED Requirements

### Requirement: Dates MUST be ISO 8601

`GeneralSchemaOrgMapper` MUST pass `datePublished`, `dateModified` and `dateCreated` through
`middleware.payload.iso_dates.iso_date` before writing them to an Investigation or Study date. ISO 8601 dates and
date-times MUST pass unchanged. Java `Date.toString()` values with an unambiguous zone abbreviation MUST become an ISO
date-time with that zone's offset, keeping the local day, and MUST log a warning. Other values MUST NOT be written as a
date: they MUST log a warning and be kept as the Investigation Comment `Unparsed <term>`. Investigation and Study
`PublicReleaseDate` (RO-Crate `datePublished`) is the first of `datePublished`, `dateModified`, `dateCreated` that is a
date. `SubmissionDate` (RO-Crate `dateCreated`) is `dateCreated` only.

#### Scenario: e!DAL Java date

- **WHEN** `datePublished` is `Sat Jan 01 00:00:00 CET 2011`
- **THEN** Investigation and Study `PublicReleaseDate` MUST be `2011-01-01T00:00:00+01:00` and `SubmissionDate` MUST be
  empty

#### Scenario: ISO year

- **WHEN** `datePublished` is `2011`
- **THEN** `PublicReleaseDate` MUST be `2011` and no warning is logged

#### Scenario: Not a date

- **WHEN** `datePublished` is `sometime in 2011` and there is no other date
- **THEN** `PublicReleaseDate` MUST be empty and the Comment `Unparsed datePublished` MUST hold `sometime in 2011`

#### Scenario: Creation and publication dates

- **WHEN** `datePublished` is `2011-01-01` and `dateCreated` is `2010-06-30`
- **THEN** the RO-Crate root `datePublished` MUST be `2011-01-01` and `dateCreated` MUST be `2010-06-30`, also after the
  API reads the RO-Crate and writes it with `ARC.Write`

#### Scenario: No publication date

- **WHEN** there is no `datePublished`, `dateModified` is `2014` and `dateCreated` is `2010`
- **THEN** `PublicReleaseDate` MUST be `2014`
