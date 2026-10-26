# Proposal

## Why

#353: the INSPIRE mapper's Study protocols (Data Acquisition, Data Processing) add `Input/Output [Data]` columns with
hardcoded `"Raw Data"` / `"Processed Data"` cells. INSPIRE CSW records carry metadata only, so these files do not exist in
the source. arctrl serialises them as `@type: File` nodes under `studies/<id>/resources/`, and the API catalog finalize
logs a WARNING for each one on every BonaRes ARC.

## What Changes

- Data Acquisition and Data Processing protocol tables no longer have Data input or output columns; their parameter
  columns stay as they are.
- The minimal Data Processing table (only an invented "Note" between the two Data cells) is no longer emitted.
- The Assay annotation table (`Output [URI]`) is unchanged.
- **Non-goals:** the same placeholders in the schema.org and Regal mappers; the "Selected Location" sample input; the
  Assay `<slug>_dataset` fallback. Each is a follow-up.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `inspire-to-arc-mapping`: Study protocol tables MUST NOT invent Data entities.

## Impact

- `middleware/payload/src/middleware/payload/inspire/mapper.py` and its tests
- `docs/mappers/inspire.md` if it describes Study protocol I/O
