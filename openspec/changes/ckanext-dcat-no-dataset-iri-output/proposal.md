# Proposal

## Why

#353 removed invented data entities from the harvested ARCs. The `ckanext_dcat` mapper still fills the Assay
`Measurement` table's `Output [URI]` with the `dcat:Dataset` IRI when the dataset has no distribution access or download
URL. For ckanext-dcat that IRI is the CKAN dataset page, i.e. metadata, not data, and it already appears as the
Investigation `Landing Page` comment. On live SRADI 25 of 57 datasets hit this fallback (checked 2026-10-29). The
INSPIRE mapper dropped the same kind of fallback in `inspire-no-invented-output-uri`.

## What Changes

- When a `dcat:Dataset` has no distribution `dcat:accessURL` / `dcat:downloadURL`, the Assay table has no `Output [URI]`
  column. It keeps one row with `Input [Source Name]` and the distribution comments the dataset has.
- Datasets with a distribution URL are unchanged: `Output [URI]` is the first URL.
- **Non-goals:** blank-node `dcat:Dataset` subjects (the `dcat_ap` protocol only discovers datasets with an IRI); the
  `"Dataset Source"` `Input [Source Name]` placeholder; the INSPIRE and schema.org mappers; logging datasets without
  distributions (valid input).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `ckanext-dcat-to-arc-mapping`: the Assay `Output [URI]` comes only from a distribution URL; no dataset IRI fallback.

## Impact

- `middleware/payload` `ckanext_dcat` mapper and its tests; `docs/mappers/ckanext-dcat.md` (distribution row and
  mapping-rules list).
- SRADI ARCs without distribution URLs lose a `URI` entity that repeated the landing page.
