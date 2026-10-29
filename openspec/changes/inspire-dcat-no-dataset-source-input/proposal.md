# Proposal

## Why

#353 removed invented data entities from the harvested ARCs. The INSPIRE and `ckanext_dcat` mappers still start every
Assay `Measurement` table with `Input [Source Name] = "Dataset Source"`. That value is not in any source record, and no
commit says why it was added (bda19a6). arctrl serialises it as `{"@id": "#Source_Dataset_Source", "@type": "Sample",
"additionalType": "Source"}`, so every INSPIRE and DCAT-AP ARC has the same made-up sample. arctrl does not need it: a
table without an Input column serialises to a `LabProcess` with `object: []`.

## What Changes

- The INSPIRE and `ckanext_dcat` Assay tables no longer have an `Input [Source Name]` column.
- When the table would then have no columns (no `Output [URI]`, no comments), the Assay has no annotation table.
- `Output [URI]` and the Assay comments are unchanged.
- **Non-goals:** the schema.org, Regal and PhenoROAM mappers (same literal, tracked separately); the INSPIRE Spatial
  Sampling `Input [Source Name] = "Geographic Region"`; linking the Assay input to the Study `Selected Location`
  sample; the hardcoded INSPIRE `TechnologyPlatform`.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `inspire-to-arc-mapping`: the Assay table has no invented input and is omitted when empty.
- `ckanext-dcat-to-arc-mapping`: the same for the distribution table.

## Impact

- `middleware/payload` INSPIRE and `ckanext_dcat` mappers and their tests; `docs/mappers/inspire.md` and
  `docs/mappers/ckanext-dcat.md`.
- Every INSPIRE and DCAT-AP ARC loses the `#Source_Dataset_Source` entity; records with no Assay data lose the empty
  `Measurement` process.
