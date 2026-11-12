# Spec Delta

## ADDED Requirements

### Requirement: Study Bounding Box ParameterValue MUST use schema.org box order

When `InspireRecord.spatial_extent` is a four-number bbox (`west`, `south`, `east`, `north` — OWSLib
`minx,miny,maxx,maxy`), `InspireMapper` MUST set the Study Spatial Sampling protocol parameter named `Bounding Box` to
the schema.org `GeoShape.box` string `south west north east` (four numbers separated by single spaces; no brackets). The
mapper MUST NOT write INSPIRE west/south/east/north order or a bracketed list into that ParameterValue.
`docs/mappers/inspire.md` MUST document this ARC contract and the conversion from `EX_GeographicBoundingBox`.

#### Scenario: INSPIRE bbox becomes schema.org box string

- **WHEN** a record has `spatial_extent` `[10.0, 48.0, 11.0, 49.0]` (west, south, east, north)
- **THEN** the Spatial Sampling `Bounding Box` ParameterValue MUST be `48.0 10.0 49.0 11.0`

#### Scenario: No spatial extent omits Bounding Box

- **WHEN** a geographic record has no `spatial_extent` but still emits Spatial Sampling for other parameters
- **THEN** the protocol MUST NOT include a `Bounding Box` parameter
