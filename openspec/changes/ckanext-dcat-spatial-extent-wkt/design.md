# Design

## Context

`docs/mappers/ckanext-dcat.md` documents `Spatial Extent` as fixed text. The placeholder guarded against very large
geometries. #557 asks for the coordinates so the Search Hub can test map display.

## Decisions

- **WKT, not GeoJSON.** WKT is the GeoSPARQL literal DCAT-AP recommends, names the geometry type in the same string (so
  no second comment), and is the smaller of the two on SRADI. SRADI rounds its WKT to 4 decimals; that is reported to
  the provider (SRADI metadata feedback), not worked around.
- **Cap as config, default 10,000.** Config defaults live in the pydantic model (no hidden fallbacks). 10,000 passes
  every SRADI geometry seen (max 8,482) and keeps a pathological polygon out of the ARC and the dump.
- **Placeholder kept** for over-cap and no-WKT cases, so consumers still learn that a geometry exists at the source.
- **Several literals** are sorted for deterministic output and joined with `"; "` (WKT uses commas internally).

## Risks

- The API may split comment text on some separator; checked during the manual SRADI harvest (task 2.1).
