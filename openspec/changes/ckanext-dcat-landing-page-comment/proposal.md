# Proposal

## Why

#531: SRADI records in the Search Hub have no link back to their landing page. The schema.org and Regal mappers write
the Investigation comment `Landing Page` since #534; the `ckanext_dcat` mapper does not, so DCAT-AP ARCs carry no
landing page for the API to export as `schema:url` (fairagro/m4.2_advanced_middleware_api#617). SRADI's DCAT export has
no `dcat:landingPage`, but its dataset IRIs (`https://agrihub.gis.lrg.tum.de/dataset/<uuid>`) are the CKAN dataset
pages, as ckanext-dcat builds them by default.

## What Changes

- The `ckanext_dcat` mapper adds one Investigation comment `Landing Page`: the first http(s) `dcat:landingPage` in a
  deterministic order, else the dataset IRI when it is http(s), else no comment.
- No `URL` comment is added for DCAT-AP (it is due to be dropped for schema.org once API #617 is live).
- **Non-goals:** the API export (#617); dropping the schema.org `URL` comment; checking at harvest time that the URL
  resolves; RDI-specific URL patterns.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `ckanext-dcat-to-arc-mapping`: the Investigation carries the dataset landing page as a `Landing Page` comment.

## Impact

- `middleware/payload` `ckanext_dcat` mapper and its tests; `docs/mappers/ckanext-dcat.md` (field table).
