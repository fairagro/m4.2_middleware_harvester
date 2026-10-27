# Proposal

## Why

#353: when an INSPIRE record has neither a `dataSetURI` nor online resources, the Assay annotation table falls back to
`Output [URI]` = `<slug>_dataset`. arctrl serialises that as a `{"@type": "URI"}` entity with `@id`
`URI=<slug>_dataset`, which is not a resolvable URI and not present in the `InspireRecord`. Consumers can read it as a
real data location.

## What Changes

- The Assay annotation table has an `Output [URI]` column only when the record has a `dataSetURI` or at least one online
  resource. Otherwise the column is omitted; the table keeps its single row with `Input [Source Name]` and any Graphic
  Overview comment.
- `dataSetURI` (preferred) and first-online-resource (fallback) behaviour is unchanged, including the Online Resource
  comments skipping the promoted URL.
- No log or warning for records without a URI: this is valid input.
- `docs/mappers/inspire.md` and the `_create_assay_table` docstring drop the `<slug>_dataset` last resort.
- **Non-goals:** the `"Dataset Source"` Assay input placeholder; the hardcoded `TechnologyPlatform`; linked-data
  mappers; a `urn:` derived from `fileIdentifier`.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `inspire-to-arc-mapping`: the Assay `Output [URI]` MUST NOT be invented.

## Impact

- `middleware/payload/src/middleware/payload/inspire/mapper.py` and its tests
- `docs/mappers/inspire.md`
