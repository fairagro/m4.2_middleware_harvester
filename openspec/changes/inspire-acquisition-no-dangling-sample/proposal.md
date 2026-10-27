# Proposal

## Why

#353: the INSPIRE Data Acquisition protocol table always has an `Input [Sample]` column with the cell "Selected
Location". That sample is the output of the Spatial Sampling protocol, but Spatial Sampling is not emitted for
`nonGeographicDataset` records or for records without bounding box, CRS or resolution. In those ARCs the sample is
consumed by Data Acquisition and created by nothing.

## What Changes

- The Data Acquisition table has its `Input [Sample]` "Selected Location" column only when the Spatial Sampling
  protocol is emitted for the record. Otherwise the table carries parameter columns only, like Data Processing.
- Data Acquisition parameters (Temporal Extent, Acquisition Date) are unchanged.
- `docs/mappers/inspire.md` states the condition on the Protocol 2 Input line.
- **Non-goals:** Spatial Sampling's own input and output; the Assay `<slug>_dataset` fallback; Regal Spatial Sampling.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `inspire-to-arc-mapping`: Study protocol tables MUST NOT reference samples that no protocol produces.

## Impact

- `middleware/payload/src/middleware/payload/inspire/mapper.py` and its tests
- `docs/mappers/inspire.md`
