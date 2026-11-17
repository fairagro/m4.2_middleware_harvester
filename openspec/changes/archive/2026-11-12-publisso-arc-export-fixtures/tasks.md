# Tasks

## 1. Curate and generate publisso crates

- [x] 1.1 Select 2–4 complementary live PUBLISSO/Regal records (distinct edges: person/agent given-name, license,
      subjects±DDC, funding/org) using `dev_environment` publisso config — verify each chosen `/find` or resource URL
      resolves
- [x] 1.2 Map each record through the real publisso client path (`regal_find` + jsonld parser + `RegalMapper`), write
      `middleware/harvester/tests/fixtures/arc_export/publisso/<case-id>/ro-crate-metadata.json`, redact emails/phones —
      verify files exist and are non-synthetic (real Investigation identifiers / DOIs / FRL ids); keep root smoke crate
- [x] 1.3 Add `fixtures/arc_export/publisso/README.md` listing case ids and covered features — verify it matches
      committed directories

## 2. Docs and system_local gate

- [x] 2.1 Update `docs/arc-export-fixtures.md` publisso status from deferred #611 to landed (point at nested cases +
      README) — verify the status table no longer says Deferred for publisso
- [x] 2.2 Extend `system_local` presence assertion so publisso has ≥2 nested real-data cases (mirror bonares/edal) —
      verify `uv run pytest -m system_local middleware/harvester/tests/system_local -v` passes with Docker

## 3. Integration

- [x] 3.1 Run `openspec validate publisso-arc-export-fixtures` and focused fixture discovery / `system_local` checks —
      verify green / no OpenSpec errors
