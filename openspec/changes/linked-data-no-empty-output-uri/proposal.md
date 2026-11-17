# Proposal

## Why

#353 removed invented entities from the harvested ARCs. INSPIRE (`inspire-no-invented-output-uri`) and DCAT-AP
(`ckanext-dcat-no-dataset-iri-output`) already omit `Output [URI]` when the record has no URL. The schema.org and MODS
mappers still write `Output [URI] = ""` in that case, so the ARC carries an empty `URI` entity that names nothing.

## What Changes

- The schema.org and MODS Assay tables have an `Output [URI]` column only when a URL is known. The URL resolution
  itself is unchanged.
- When the Assay table would then have no columns, the Assay has no annotation table (as INSPIRE).
- The PhenoROAM mapper has the same `""` fallback, but it is unreachable: a record with neither `itemUUID` nor a
  harvest source id is refused before the Assay is built, so the Assay table always has a landing URL. The dead
  fallback is removed; behaviour does not change and there is no spec delta.
- **Non-goals:** new URI fallbacks (e.g. MODS → DOI); the Regal mapper, which fails a record without a URI.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `schemaorg-to-arc-mapping`: no empty `Output [URI]`.
- `mods-to-arc-mapping`: the same.

## Impact

- `middleware/payload` schema.org and MODS mappers and their tests; the PhenoROAM mapper (dead fallback only);
  `docs/mappers/*.md` for schema.org and MODS.
- Only records without any known URL change; expected to be rare in live harvests.
