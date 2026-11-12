# Tasks

## 1. Curate and generate openagrar crates

- [ ] 1.1 Select 2–4 complementary live OpenAgrar MODS records (distinct edges: multi-Person creators/affiliation,
      organization/corporate name when present, license + subjects/keywords, title/identifier/related-item shapes) via
      the preferred `mycore_rest` entry URL — verify each chosen object id resolves over live `/api/v2/objects/{id}`
- [ ] 1.2 Map each record through the real openagrar client path (`mycore_rest` + `mods_xml` + `mods_general`), write
      `middleware/harvester/tests/fixtures/arc_export/openagrar/<case-id>/ro-crate-metadata.json`, redact emails/phones
      — verify files exist and are non-synthetic (real MyCoRe ids / DOIs / titles)
- [ ] 1.3 Delete the root smoke crate `fixtures/arc_export/openagrar/ro-crate-metadata.json` and add
      `fixtures/arc_export/openagrar/README.md` listing case ids and covered features — verify only nested
      `<case-id>/ro-crate-metadata.json` crates remain under `openagrar/` and the README matches them

## 2. Docs and system_local gate

- [ ] 2.1 Update `docs/arc-export-fixtures.md` openagrar (live / MODS) status from deferred #614 to landed (point at
      nested cases + README; note smoke removed; keep `openagrar-fixture` as stand-in-only) — verify the status table no
      longer says Deferred for openagrar (live / MODS)
- [ ] 2.2 Extend `system_local` presence assertion so openagrar has ≥2 nested real-data cases (mirror
      bonares/edal/publisso/plabipd) — verify `uv run pytest -m system_local middleware/harvester/tests/system_local -v`
      passes with Docker

## 3. Integration

- [ ] 3.1 Run `openspec validate openagrar-arc-export-fixtures` and focused fixture discovery / `system_local` checks —
      verify green / no OpenSpec errors
