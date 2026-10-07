## Why

Search Hub reads `dateModified` from the DataHUB basic-layout dumps to show when a dataset last changed, but no record
of the first-phase RDIs had one: no mapper wrote it (raised in Julian Schneider's Search Hub review). Tracked as GitHub
[#415](https://github.com/fairagro/m4.2_middleware_harvester/issues/415).

ARCtrl ≥ 3.2 (harvester 3.2.1, API 3.2.2, after the fix for nfdi4plants/ARCtrl#623) writes `SubmissionDate` as
`dateCreated`, `PublicReleaseDate` as `datePublished`, and an Investigation Comment named `dateModified` as the RO-Crate
root `dateModified` (reading it back into that Comment). So the source modification date can be carried without an API
change.

## What Changes

- New `middleware.payload.arc_dates.date_modified_comment`: the `dateModified` Comment from an ISO 8601 or Java `Date`
  value (via `iso_date`), else none. Only source dates, never the harvest time (that is `sdDatePublished`).
- Schema.org: `schema:dateModified`.
- INSPIRE: the latest citation `CI_Date` of type `revision`. `gmd:dateStamp` stays the `Metadata Date` Comment and is
  never `dateModified` (resource dates only, decided with the maintainer).
- Regal: `isDescribedBy.modified` (`ore:isDescribedBy` → `dcterms:modified`), when the repository object last changed;
  Regal has no other modification date.

Out of scope: #407 (which ARC field carries the source publication date). The ARCtrl finding above makes it a
harvester-only change too; it stays a separate issue.

## Capabilities

### Modified Capabilities

- `schemaorg-to-arc-mapping`, `inspire-to-arc-mapping`, `regal-to-arc-mapping`: source `dateModified`.

## Impact

- Live Publisso (92): all get `dateModified` (e.g. `2024-09-04T09:34:30.938+0200`); no other ARC change.
- Live BonaRes + Thünen (425): no `revision` dates in the source, so no `dateModified`; unchanged.
- e!DAL publishes no `dateModified`; OpenAgrar (blocked live, #271) gets it if its schema.org has one.
