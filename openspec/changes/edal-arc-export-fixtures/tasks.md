# Tasks

## 1. Curate and generate edal crates

- [ ] 1.1 Select 2–4 complementary live e!DAL records (distinct edges: person/ORCID or flat address,
      license/placeholder, org-only and/or DOI/`@id`) using `dev_environment` edal config — verify each chosen
      DOI/landing URL resolves
- [ ] 1.2 Map each record through the real edal client path (generic + schema.org / configured placeholders), write
      `middleware/harvester/tests/fixtures/arc_export/edal/<case-id>/ro-crate-metadata.json`, redact emails/phones —
      verify files exist and are non-synthetic (real Investigation identifiers / DOIs)
- [ ] 1.3 Add `fixtures/arc_export/edal/README.md` listing case ids and covered features — verify it matches committed
      directories

## 2. Docs and system_local gate

- [ ] 2.1 Update `docs/arc-export-fixtures.md` edal status from deferred #610 to landed (point at nested cases + README)
      — verify the status table no longer says Deferred for edal
- [ ] 2.2 Extend `system_local` presence assertion so edal has ≥2 nested real-data cases (mirror bonares) when that
      check exists on the #600 tip — verify `uv run pytest -m system_local middleware/harvester/tests/system_local -v`
      passes with Docker

## 3. Integration

- [ ] 3.1 Run `openspec validate edal-arc-export-fixtures` (or equivalent) and focused fixture discovery tests — verify
      green / no OpenSpec errors
