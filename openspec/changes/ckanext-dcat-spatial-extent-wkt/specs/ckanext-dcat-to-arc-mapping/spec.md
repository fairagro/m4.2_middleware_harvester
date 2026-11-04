# Spec Delta

## ADDED Requirements

### Requirement: Spatial Extent MUST carry the WKT geometry

When a `dcat:Dataset` has `dct:spatial`, the ckanext-dcat mapper MUST add the Investigation comment `Spatial Extent`.
Its text MUST be the distinct `locn:geometry` literals typed `gsp:wktLiteral` of the `dct:spatial` location(s),
verbatim, sorted and joined with `"; "`. When there is no such literal, or the joined text is longer than
`mapper.ckanext_dcat.spatial_extent_max_chars` (default 15,000), the text MUST be the placeholder
`Geographic extent provided by the source RDI (see the RDI record).`; over the cap the mapper MUST log a WARNING naming
the dataset and the length. A dataset without `dct:spatial` MUST NOT get the comment.

#### Scenario: Point geometry

- **GIVEN** a `dcat:Dataset` whose `dct:spatial` location has `locn:geometry "POINT (11.69 48.40)"^^gsp:wktLiteral`
- **WHEN** it is mapped
- **THEN** the Investigation comment `Spatial Extent` is `POINT (11.69 48.40)`

#### Scenario: Geometry over the cap

- **GIVEN** a `dcat:Dataset` whose WKT literal is longer than `spatial_extent_max_chars`
- **WHEN** it is mapped
- **THEN** `Spatial Extent` is the placeholder, the WKT is not in the ARC, and a WARNING names the dataset and the
  length

#### Scenario: No WKT literal

- **GIVEN** a `dcat:Dataset` whose `dct:spatial` location has only a GeoJSON `locn:geometry`
- **WHEN** it is mapped
- **THEN** `Spatial Extent` is the placeholder

#### Scenario: Several WKT literals

- **GIVEN** a `dcat:Dataset` whose location has the WKT literals `POINT (2 2)` and `POINT (1 1)`
- **WHEN** it is mapped
- **THEN** `Spatial Extent` is `POINT (1 1); POINT (2 2)`

#### Scenario: No dct:spatial

- **GIVEN** a `dcat:Dataset` without `dct:spatial`
- **WHEN** it is mapped
- **THEN** the Investigation has no `Spatial Extent` comment

#### Scenario: Configured cap

- **GIVEN** `mapper.ckanext_dcat.spatial_extent_max_chars: 50` and a 100-character WKT literal
- **WHEN** the dataset is mapped
- **THEN** `Spatial Extent` is the placeholder
