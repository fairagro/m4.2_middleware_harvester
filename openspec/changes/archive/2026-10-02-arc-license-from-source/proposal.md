## Why

No mapper set `ARC.License`, so ARCtrl's RO-Crate writer emitted its default `#LICENSE` node ("ALL RIGHTS RESERVED BY
THE AUTHORS") for every harvested ARC, including CC-BY, CC0, ODC-By and dl-de/by data. The real licence was only kept as
a Comment. Tracked as GitHub [#404](https://github.com/fairagro/m4.2_middleware_harvester/issues/404).

## What Changes

- New shared helper module `middleware.payload.arc_license`: `license_from_value` (Schema.org / Regal `license`) and
  `inspire_license` (ISO 19139 `gmd:otherConstraints`).
- `GeneralSchemaOrgMapper`, `RegalMapper` and `InspireMapper` pass the licence to `ARC.from_arc_investigation`.
- No source licence: the ARCtrl default stays (no licence granted means all rights reserved).
- Existing `License` / `Other Constraints` Comments are unchanged.

## Capabilities

### Modified Capabilities

- `schemaorg-to-arc-mapping`: ARC licence from `schema:license`.
- `regal-to-arc-mapping`: ARC licence from Regal `license`.
- `inspire-to-arc-mapping`: ARC licence from `gmd:otherConstraints`.

## Impact

- Every ARC with a source licence changes once after deploy (RO-Crate licence node text).
- Measured 2026-10-02: e!DAL 310/338 (28 carry the unexpanded placeholder `$licenseURL`), OpenAgrar 931/931, Publisso
  92/92, BonaRes 834/970, Thünen Atlas 51/151 (live CSW); the rest state no licence.
