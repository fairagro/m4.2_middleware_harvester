# Tasks

## 1. Curate and generate plabipd crates

- [x] 1.1 Select 2–4 complementary live PlabiPD/pubplant records (distinct edges: Organization-only creator,
      multi-Person givenName/familyName, shared-DOI collision pair when available) from `genomes.json` via
      `dev_environment` plabipd config — verify each chosen record resolves and composite discovery ids are unique
- [x] 1.2 Map each record through the real plabipd client path (`pubplant_json_array` identity + jsonld parser +
      `schema_org_general`), write
      `middleware/harvester/tests/fixtures/arc_export/plabipd/<case-id>/ro-crate-metadata.json`, redact emails/phones —
      verify files exist and are non-synthetic (real Investigation identifiers / DOIs / composite ids)
- [x] 1.3 Add `fixtures/arc_export/plabipd/README.md` listing case ids and covered features — verify it matches
      committed directories

## 2. Docs and system_local gate

- [x] 2.1 Update `docs/arc-export-fixtures.md` plabipd status from deferred #613 to landed (point at nested cases +
      README) — verify the status table no longer says Deferred for plabipd
- [x] 2.2 Extend `system_local` presence assertion so plabipd has ≥2 nested real-data cases (mirror
      bonares/edal/publisso) — verify `uv run pytest -m system_local middleware/harvester/tests/system_local -v` passes
      with Docker

## 3. Integration

- [x] 3.1 Run `openspec validate plabipd-arc-export-fixtures` and focused fixture discovery / `system_local` checks —
      verify green / no OpenSpec errors
