# Proposal

## Why

#353 removes invented entities from harvested ARCs. The INSPIRE, Regal and PhenoROAM mappers still build their Study
`Spatial Sampling` table with a hardcoded `Input [Source Name] = "Geographic Region"`. No source record contains that
value. arctrl serialises it as a `#Source_Geographic_Region` entity of `@type` `Sample`, so every BonaRes, DWD, Thünen,
Publisso and PhenoROAM ARC with spatial information carries the same made-up source.

## What Changes

- The INSPIRE, Regal and PhenoROAM `Spatial Sampling` tables no longer have an `Input [Source Name]` column.
- The parameter columns (INSPIRE `Bounding Box`, `Coordinate Reference System`, spatial resolution; Regal `Location`,
  `Coordinates`; PhenoROAM `Bounding Box`) and the `Selected Location` output are unchanged, and the table is still
  omitted when the record has no spatial information. INSPIRE Data Acquisition still takes `Selected Location` as input.
- `docs/mappers/inspire.md` and `docs/mappers/regal.md` no longer list `Geographic Region` as the protocol input.
- **Non-goals:** the `Selected Location` output sample; the leftover empty `Output [Sample Name]` in the Regal
  `Data Collection` table; aligning `Selected Location(s)` naming (each tracked separately).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `inspire-to-arc-mapping`: the Spatial Sampling table has no invented source.
- `regal-to-arc-mapping`: the same.
- `phenoroam-to-arc-mapping`: the same.

## Impact

- `middleware/payload` INSPIRE, Regal and PhenoROAM mappers and their tests; `docs/mappers/inspire.md`, `regal.md`.
- Every ARC from those mappers with spatial information loses the `#Source_Geographic_Region` entity; RO-Crate fixtures
  that contain it (BonaRes, Publisso) need regenerating.
