# Proposal

## Why

#353 removed invented entities from the harvested ARCs, and PR #555 dropped the hardcoded
`Input [Source Name] = "Dataset Source"` from the INSPIRE and `ckanext_dcat` Assays. The schema.org, Regal, MODS and
PhenoROAM mappers still start every Assay `Measurement` table with that literal. No source record contains it, and
arctrl serialises it as `{"@id": "#Source_Dataset_Source", "@type": "Sample", "additionalType": "Source"}`, so every
e!DAL, Publisso, OpenAgrar and PhenoROAM ARC carries the same made-up sample.

## What Changes

- The schema.org, Regal, MODS and PhenoROAM Assay tables no longer have an `Input [Source Name]` column.
- `Output [URI]` and the Assay comments are unchanged. These mappers always write an `Output [URI]` column, so the table
  never becomes empty.
- **Non-goals:** `Input [Source Name] = "Research Subject"` in the MODS and PhenoROAM keyword tables; an empty
  `Output [URI]` when no URL is known; the Regal and INSPIRE `"Geographic Region"` source (each tracked separately).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `schemaorg-to-arc-mapping`: the Assay table has no invented input.
- `regal-to-arc-mapping`: the same.
- `mods-to-arc-mapping`: the same.
- `phenoroam-to-arc-mapping`: the same.

## Impact

- `middleware/payload` schema.org, Regal, MODS and PhenoROAM mappers and their tests; `docs/mappers/regal.md`.
- Every e!DAL (and other schema.org RDI), Publisso, OpenAgrar and PhenoROAM ARC loses the `#Source_Dataset_Source`
  entity; RO-Crate fixtures that contain it need regenerating.
