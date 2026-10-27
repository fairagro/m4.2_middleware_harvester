# Proposal

## Why

#534: the basic-layout export (API #617) publishes the Investigation comment `Landing Page` as `schema:url`. Only the
PhenoRoam mapper writes it. The schema.org (`GeneralSchemaOrgMapper`) mapper writes the landing page only as comment
`URL`, and the Regal (`RegalMapper`) mapper only uses it as the Assay `Output [URI]` fallback. Records from those RDIs
therefore have no `schema:url` in the Search Hub export.

## What Changes

- `GeneralSchemaOrgMapper` writes Investigation comment `Landing Page` with the `schema:url` value, under the same
  placeholder rules as the existing `URL` comment.
- `RegalMapper` writes Investigation comment `Landing Page` = `{resource_base_url}{@id}`.
- The `URL` comment stays until API #617 is live (deprecate before removing); the Assay `Output [URI]` is unchanged.
- **Non-goals:** SRADI / DCAT-AP landing page (#531); removing `URL`; PhenoRoam, INSPIRE, OAI-PMH; validating that
  `schema:url` is an http(s) URL.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `schemaorg-to-arc-mapping`: the Investigation carries a `Landing Page` comment from `schema:url`.
- `regal-to-arc-mapping`: the Investigation carries a `Landing Page` comment built from the record `@id`.

## Impact

- `middleware/payload/src/middleware/payload/linked_data_mapper/{general_schema_org_mapper,regal_mapper}.py` and tests
- `docs/mappers/schemaorg.md`, `docs/mappers/regal.md`
