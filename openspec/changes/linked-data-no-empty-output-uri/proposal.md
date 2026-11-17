# Proposal

## Why

#353 removed invented entities from the harvested ARCs. INSPIRE (`inspire-no-invented-output-uri`) and DCAT-AP
(`ckanext-dcat-no-dataset-iri-output`) already omit `Output [URI]` when the record has no URL. The schema.org, MODS and
PhenoROAM mappers still write `Output [URI] = ""` in that case, so the ARC carries an empty `URI` entity that names
nothing.

## What Changes

- The schema.org, MODS and PhenoROAM Assay tables have an `Output [URI]` column only when a URL is known. The URL
  resolution itself is unchanged.
- When the Assay table would then have no columns, the Assay has no annotation table (as INSPIRE).
- **Non-goals:** new URI fallbacks (e.g. MODS → DOI); the Regal mapper, which fails a record without a URI.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `schemaorg-to-arc-mapping`: no empty `Output [URI]`.
- `mods-to-arc-mapping`: the same.
- `phenoroam-to-arc-mapping`: the same.

## Impact

- `middleware/payload` schema.org, MODS and PhenoROAM mappers and their tests; `docs/mappers/*.md` for those mappers.
- Only records without any known URL change; expected to be rare in live harvests.
