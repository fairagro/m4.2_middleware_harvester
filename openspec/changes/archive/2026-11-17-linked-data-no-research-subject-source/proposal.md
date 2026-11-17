# Proposal

## Why

#353 removes invented entities from harvested ARCs. The schema.org, Regal, MODS and PhenoROAM mappers still build their
Study `Data Collection` table with a hardcoded `Input [Source Name] = "Research Subject"` and an empty
`Output [Sample Name] = ""`. No source record contains either value. arctrl serialises them as
`#Source_Research_Subject` and `#Sample_` entities of `@type` `Sample`, so every e!DAL, Publisso, OpenAgrar and
PhenoROAM ARC with keywords carries the same two made-up samples.

## What Changes

- The schema.org, Regal, MODS and PhenoROAM `Data Collection` tables no longer have an `Input [Source Name]` or an
  `Output [Sample Name]` column.
- The parameter columns (`Keywords`; for Regal also `Data Origin` and `Temporal Extent`) are unchanged, and the table is
  still omitted when none of them has a value.
- **Non-goals:** an empty `Output [URI]` in the Assay table; the Regal and INSPIRE `"Geographic Region"` source; moving
  keywords out of the table (each tracked separately).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `schemaorg-to-arc-mapping`: the Data Collection table has no invented source or sample.
- `regal-to-arc-mapping`: the same.
- `mods-to-arc-mapping`: the same.
- `phenoroam-to-arc-mapping`: the same.

## Impact

- `middleware/payload` schema.org, Regal, MODS and PhenoROAM mappers and their tests.
- Every ARC from those mappers that has keywords (Regal: or data origin / recording period) loses the
  `#Source_Research_Subject` and `#Sample_` entities; RO-Crate fixtures that contain them need regenerating.
