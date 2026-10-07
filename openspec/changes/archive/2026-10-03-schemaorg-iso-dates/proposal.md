## Why

e!DAL emits `datePublished` as a Java `Date.toString()` value (`Sat Jan 01 00:00:00 CET 2011`), and
`GeneralSchemaOrgMapper` copied any `datePublished` / `dateModified` string into `SubmissionDate` unchecked. All 338
e!DAL records in the DataHUB export had a non-ISO date. Tracked as GitHub
[#409](https://github.com/fairagro/m4.2_middleware_harvester/issues/409).

## What Changes

- New shared helper `middleware.payload.iso_dates.iso_date`: ISO 8601 dates / date-times pass unchanged (same shape as
  the INSPIRE `IsoDate` type); Java `Date.toString()` with an unambiguous zone abbreviation becomes an ISO date-time
  with that offset (local day kept); anything else is `None`.
- Schema.org mapper: Investigation `SubmissionDate` is the first of `datePublished`, `dateModified` that is a date;
  Study `SubmissionDate` is `datePublished` if it is a date. Normalised values log a warning; non-dates log a warning
  and become the Comment `Unparsed <term>`.

## Capabilities

### Modified Capabilities

- `schemaorg-to-arc-mapping`: ISO 8601 dates.

## Impact

- e!DAL ARCs change once after deploy. Live e!DAL (338 records): all 338 Java dates normalised, 0 unparsed. Other
  Schema.org sources already use ISO shapes (year, date, date-time) and are unchanged.
