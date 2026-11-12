# Proposal

## Why

Middleware catalog materialize (API #553 / PR #687) builds root Dataset `spatialCoverage` (`GeoShape.box`) from Study
ParameterValues named `Bounding Box`. The value contract is **schema.org box order**: `south west north east`. Mappers
must normalize source encodings before writing ARC — middleware will not reinterpret INSPIRE west/south/east/north.

INSPIRE today writes `[minx, miny, maxx, maxy]` (west, south, east, north) into that parameter, so BonaRes/Thünen dumps
lack usable spatial coverage. PhenoRoam has a four-side bbox but only an Assay comment, not Study `Bounding Box`.

## What Changes

- **INSPIRE:** Convert `spatial_extent` `[west, south, east, north]` to schema.org `south west north east` (space-
  separated string) for Study Spatial Sampling parameter `Bounding Box`; stop emitting the bracketed W/S/E/N list.
- **PhenoRoam:** When `pr:blockBBox` has usable sides, emit Study Spatial Sampling with parameter `Bounding Box` in the
  same schema.org string; stop dual-writing the Assay `Geographic Bounding Box` `W:… E:… S:… N:…` comment (single
  catalog contract).
- **Shared helper** (optional small util in `middleware.payload`) to format four floats as the schema.org box string.
- **Docs / OpenSpec:** Document the ARC ParameterValue contract and source→order conversion for INSPIRE and PhenoRoam.

### Non-goals

- **MODS / Regal / ckanext:** No four-number Study `Bounding Box` writer today (MODS geo → #547; Regal uses free-text
  Coordinates; ckanext uses Investigation Spatial Extent WKT). Do not invent bbox parsers here.
- Middleware union / export logic (#553 / #687) and per-Study dump modelling (#684).
- CRS axis-order edge cases beyond documented WGS84-style lon/lat for INSPIRE `EX_GeographicBoundingBox`.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `inspire-to-arc-mapping`: Study `Bounding Box` ParameterValue MUST be schema.org `south west north east`.
- `phenoroam-to-arc-mapping`: Usable `bbox` MUST become Study `Bounding Box` in schema.org order; Assay
  `Geographic Bounding Box` comment MUST NOT be emitted for that bbox.

## Impact

- Code: `middleware/payload/.../inspire/mapper.py`, `phenoroam/mapper.py`; optional shared formatter; unit tests;
  `docs/mappers/{inspire,phenoroam}.md`.
- Specs: deltas under `inspire-to-arc-mapping`, `phenoroam-to-arc-mapping`.
- Issue: [#631](https://github.com/fairagro/m4.2_middleware_harvester/issues/631); lock-ins A3, B1 (schema.org string),
  C1. Related #547 / #560 remain for non-box geo work.
