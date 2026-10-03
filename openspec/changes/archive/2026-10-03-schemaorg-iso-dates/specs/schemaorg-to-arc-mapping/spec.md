## ADDED Requirements

### Requirement: Dates MUST be ISO 8601

`GeneralSchemaOrgMapper` MUST pass `datePublished` and `dateModified` through `middleware.payload.iso_dates.iso_date`
before writing them to Investigation or Study `SubmissionDate`. ISO 8601 dates and date-times MUST pass unchanged. Java
`Date.toString()` values with an unambiguous zone abbreviation MUST become an ISO date-time with that zone's offset,
keeping the local day, and MUST log a warning. Other values MUST NOT be written as a date: they MUST log a warning and
be kept as the Investigation Comment `Unparsed <term>`. Investigation `SubmissionDate` is the first of `datePublished`,
`dateModified` that is a date.

#### Scenario: e!DAL Java date

- **WHEN** `datePublished` is `Sat Jan 01 00:00:00 CET 2011`
- **THEN** Investigation and Study `SubmissionDate` MUST be `2011-01-01T00:00:00+01:00`

#### Scenario: ISO year

- **WHEN** `datePublished` is `2011`
- **THEN** `SubmissionDate` MUST be `2011` and no warning is logged

#### Scenario: Not a date

- **WHEN** `datePublished` is `sometime in 2011` and there is no `dateModified`
- **THEN** `SubmissionDate` MUST be empty and the Comment `Unparsed datePublished` MUST hold `sometime in 2011`
