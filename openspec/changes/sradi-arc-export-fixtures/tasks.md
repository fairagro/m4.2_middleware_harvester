# Tasks

## 1. Curate and generate sradi crates

- [ ] 1.1 Select 2–4 complementary live SRADI `dcat:Dataset` records (distinct edges: multi-distribution / formats,
      spatial WKT, org publisher/contact unwrap, landing page / identifier, with vs without `dcterms:license` when
      available) from `https://agrihub.gis.lrg.tum.de/catalog.jsonld?fq=groups:dataset` via Hydra pagination — verify
      each chosen package/dataset IRI resolves
- [ ] 1.2 Map each record through the real sradi client path (`dcat_ap` + `jsonld` + `ckanext_dcat`), write
      `middleware/harvester/tests/fixtures/arc_export/sradi/<case-id>/ro-crate-metadata.json`, redact emails — verify
      files exist and are non-synthetic (real Investigation identifiers / package slugs / landing pages)
- [ ] 1.3 Add `fixtures/arc_export/sradi/README.md` listing case ids and covered features; confirm no root smoke crate —
      verify only nested `<case-id>/ro-crate-metadata.json` crates exist under `sradi/` and the README matches them

## 2. Docs and system_local gate

- [ ] 2.1 Update `docs/arc-export-fixtures.md` sradi status from deferred #612 to landed (point at nested cases +
      README) — verify the status table no longer says Deferred for sradi
- [ ] 2.2 Extend `system_local` presence assertion so sradi has ≥2 nested real-data cases (mirror siblings) — verify
      `uv run pytest -m system_local middleware/harvester/tests/system_local -v` passes with Docker

## 3. Integration

- [ ] 3.1 Run `openspec validate sradi-arc-export-fixtures` and focused fixture discovery / `system_local` checks —
      verify green / no OpenSpec errors

## Workflow follow-up

- Archive the change after the project's review requirements are satisfied.
- Verify the archived result.
