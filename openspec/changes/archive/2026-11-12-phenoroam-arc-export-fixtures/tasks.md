# Tasks

## 1. Curate and generate phenoroam crates

- [x] 1.1 Select 2–4 complementary live PhenoRoam records (distinct edges: bbox vs none, multi-Person
      contacts/affiliation, keywords/license, datafile links and/or study-parent titles) via OAI-PMH
      `ListIdentifiers`/`GetRecord` with `metadataPrefix=phenoroam` — verify each chosen UUID resolves
- [x] 1.2 Map each record through the real phenoroam client path (`oai_pmh` + `phenoroam_xml` + `phenoroam_general`),
      write `middleware/harvester/tests/fixtures/arc_export/phenoroam/<case-id>/ro-crate-metadata.json`, redact emails —
      verify files exist and are non-synthetic (real catalog UUIDs / titles)
- [x] 1.3 Add `fixtures/arc_export/phenoroam/README.md` listing case ids and covered features; confirm no root smoke
      crate — verify only nested `<case-id>/ro-crate-metadata.json` crates exist under `phenoroam/` and the README
      matches them

## 2. Docs and system_local gate

- [x] 2.1 Update `docs/arc-export-fixtures.md` phenoroam status from deferred #615 to landed (point at nested cases +
      README) — verify the status table no longer says Deferred for phenoroam
- [x] 2.2 Extend `system_local` presence assertion so phenoroam has ≥2 nested real-data cases (mirror siblings) — verify
      `uv run pytest -m system_local middleware/harvester/tests/system_local -v` passes with Docker

## 3. Integration

- [x] 3.1 Run `openspec validate phenoroam-arc-export-fixtures` and focused fixture discovery / `system_local` checks —
      verify green / no OpenSpec errors
