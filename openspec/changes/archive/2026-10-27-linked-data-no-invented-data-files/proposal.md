# Proposal

## Why

#353 follow-up: the schema.org (`GeneralSchemaOrgMapper`) and Regal (`RegalMapper`) Study "Data Processing" protocols
add `Input/Output [Data]` columns with hardcoded `"Raw Data"` / `"Published Dataset"` cells, and the ckanext-dcat
(`CkanextDcatMapper`) "Dataset Processing" protocol adds a `"Raw Data"` Source input and a `"Published Dataset"` Data
output. The harvested records carry metadata only, so these entities do not exist in the source. arctrl serialises the
Data cells as `@type: File` nodes under `studies/<id>/resources/`. The INSPIRE mapper was fixed in
`inspire-no-invented-data-files`.

## What Changes

- The schema.org and Regal Data Processing tables and the ckanext-dcat Dataset Processing table no longer have input or
  output columns; their parameter columns stay as they are.
- The Assay annotation table (`Output [URI]`) is unchanged.
- **Non-goals:** the fixed Processing Description notes; the Data Collection "Research Subject" Source and empty Sample
  output; the INSPIRE Assay `<slug>_dataset` fallback.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `schemaorg-to-arc-mapping`: the Data Processing protocol MUST NOT invent input/output entities.
- `regal-to-arc-mapping`: the Data Processing protocol MUST NOT invent input/output entities.
- `ckanext-dcat-to-arc-mapping`: the Dataset Processing protocol MUST NOT invent input/output entities.

## Impact

- `middleware/payload/src/middleware/payload/linked_data_mapper/{general_schema_org_mapper,regal_mapper,ckanext_dcat_mapper}.py`
  and their tests
- `docs/mappers/ckanext-dcat.md` (Processing row describes the invented input/output)
