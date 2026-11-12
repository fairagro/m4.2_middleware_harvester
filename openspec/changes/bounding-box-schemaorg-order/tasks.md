# Tasks

## 1. Shared schema.org box helper

- [ ] 1.1 Add a small helper (e.g. `middleware.payload.geo.schema_org_box`) that formats west/south/east/north floats as
      `south west north east`, returning `None` if any value is missing/unparseable — verify with unit tests for a happy
      path and an incomplete input

## 2. INSPIRE Study Bounding Box

- [ ] 2.1 In `InspireMapper` Spatial Sampling, write `Bounding Box` via the helper from `spatial_extent` — verify unit
      tests expect `48.0 10.0 49.0 11.0` (update any `[10.0, 48.0, …]` assertions)
- [ ] 2.2 Update `docs/mappers/inspire.md` Bounding Box row/protocol notes for schema.org order — verify wording matches
      the inspire delta scenarios

## 3. PhenoRoam Study Bounding Box

- [ ] 3.1 Emit Study Spatial Sampling with `Bounding Box` from `record.bbox` via the helper; remove Assay
      `Geographic Bounding Box` comment path — verify unit/fixture tests for full bbox string and incomplete omit
- [ ] 3.2 Update `docs/mappers/phenoroam.md` bbox row for Study `Bounding Box` — verify wording matches the phenoroam
      delta scenarios

## 4. Quality

- [ ] 4.1 Run focused inspire/phenoroam/geo unit tests and `ruff format` / `ruff check` on touched files — verify green
- [ ] 4.2 `openspec validate bounding-box-schemaorg-order --strict` — verify passes
