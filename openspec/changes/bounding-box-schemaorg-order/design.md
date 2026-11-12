# Design

## Context

See `proposal.md` — Why. schema.org [`GeoShape.box`](https://schema.org/box): two lat/lon pairs as
`south west north east` (whitespace-separated). INSPIRE `EX_GeographicBoundingBox` / OWSLib `bbox` is
`minx,miny,maxx,maxy` = west, south, east, north. PhenoRoam `pr:blockBBox` exposes W/E/S/N strings.

## Goals / Non-Goals

**Goals:** One ParameterValue name (`Bounding Box`) and one value grammar (schema.org SWNE string) for every mapper that
can emit a four-number box in this PR (INSPIRE + PhenoRoam).

**Non-Goals:** Parsing WKT/GeoJSON into boxes; MODS/Regal/ckanext inventing boxes; keeping Assays as the catalog spatial
surface for PhenoRoam.

## Decisions

1. **Value shape = space-separated `south west north east` (B1)** Matches schema.org `GeoShape.box` and the middleware
   #553 contract. Prefer over bracketed lists / comma lists so dumps and docs share one prose form. Alternatives
   rejected: keep `[w,s,e,n]` (wrong order); `[s,w,n,e]` brackets (non-standard vs GeoShape.box text).

2. **Shared formatter `schema_org_box(west, south, east, north) -> str`** Single helper used by INSPIRE (from
   `spatial_extent`) and PhenoRoam (from bbox sides). Returns `None` if any required float is missing/unparseable.
   Rationale: one grammar, two sources. Alternative rejected: duplicate f-strings per mapper.

3. **PhenoRoam: Study Spatial Sampling + drop Assay Geographic Bounding Box comment** Catalog reads Study `Bounding Box`
   only. Dual Assay comment in WENS labels would confuse operators and diverge. Alternative rejected: keep both formats.

4. **MODS / Regal / ckanext: document-only non-goals** A3 means “every writer that can produce a 4-number box” — those
   mappers cannot today without new geo parsing (#547).

## Risks / Trade-offs

- [INSPIRE CRS not lon/lat] → Document WGS84-style assumption; out of scope to reproject.
- [PhenoRoam partial sides] → Only emit when all four sides parse to floats (fail soft: omit Bounding Box).
- [Existing tests assert `[10.0, 48.0, …]`] → Update to `48.0 10.0 49.0 11.0`.

## Migration Plan

Ship with harvester image; re-harvest updates ParameterValues. Rollback = revert mapper commits.
