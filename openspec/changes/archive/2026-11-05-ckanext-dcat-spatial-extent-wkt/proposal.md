# Proposal

## Why

The `ckanext_dcat` mapper writes a fixed placeholder into the Investigation comment `Spatial Extent` ("Geographic extent
provided by the source RDI (see the RDI record).") whenever a dataset has `dct:spatial`. The placeholder was chosen in
6c32aca to keep very large geometries out of the ARC. The Search Hub team needs the actual geometry to place SRADI
datasets on a map (#557). SRADI's DCAT export carries it as `locn:geometry` WKT (`gsp:wktLiteral`) and as GeoJSON: 58 of
the first 100 catalogue entries have one (39 `MULTIPOLYGON`, 19 `POINT`; WKT length median about 100, maximum 8,482
characters).

## What Changes

- `Spatial Extent` carries the `locn:geometry` WKT literal(s) of the dataset's `dct:spatial` location verbatim; several
  distinct literals are sorted and joined with `"; "`.
- A new `mapper.ckanext_dcat.spatial_extent_max_chars` setting (default 15,000) caps the comment. Above the cap, and
  when the location has no WKT literal, the mapper keeps the placeholder; above the cap it logs a WARNING.
- **Non-goals:** GeoJSON output, a separate geometry-type comment, `dcat:bbox` / `dcat:centroid`, schema.org `Place` /
  `GeoShape` modelling across RDIs, and SRADI's 4-decimal WKT rounding (provider side).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `ckanext-dcat-to-arc-mapping`: `Spatial Extent` carries the WKT geometry, capped by configuration.

## Impact

- `middleware/payload`: `ckanext_dcat` mapper, its type config and tests; `docs/mappers/ckanext-dcat.md`.
- SRADI ARCs with a geometry get the WKT instead of the placeholder in `Spatial Extent`; no other field changes.
