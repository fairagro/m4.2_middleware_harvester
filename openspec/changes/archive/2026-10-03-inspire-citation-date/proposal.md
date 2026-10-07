## Why

`InspireMapper` set the Investigation and Study `SubmissionDate` from `gmd:dateStamp`, the time the metadata record was
last changed, so every BonaRes and Thünen ARC showed a 2026 date. The dataset dates are the citation `CI_Date` entries.
Tracked as GitHub [#408](https://github.com/fairagro/m4.2_middleware_harvester/issues/408).

## What Changes

- Investigation and Study `SubmissionDate` come from the citation dates: earliest publication, else latest revision,
  else earliest creation; empty without any.
- `dateStamp` becomes the Investigation Comment `Metadata Date`.
- Which ARC field carries publication vs. creation date in the exported RO-Crate is still open in #407 (with the API
  team); this change keeps the field the Schema.org mapper uses.

## Capabilities

### Modified Capabilities

- `inspire-to-arc-mapping`: dataset date from the citation.

## Impact

- Every INSPIRE ARC changes once after deploy. Live Thünen (151 records): every date is now the citation date
  (2020–2026); none equals `dateStamp`.
