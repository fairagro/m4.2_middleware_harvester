# Tasks

## 1. Gate discovery + docs

- [x] 1.1 Extend `system_local` fixture discovery so each leaf directory containing `ro-crate-metadata.json` under
      `tests/fixtures/arc_export/` is parametrized (support `<rdi>/<case>/…` while keeping today’s
      `<rdi>/ro-crate-metadata.json` smoke paths) — verify existing smoke fixtures still collect and the three-family
      presence assertion still passes
- [x] 1.2 Update `docs/arc-export-fixtures.md` for real-data generation (curate → map → commit), coverage notes,
      optional Git LFS, redaction, and coexistence with smoke crates — verify the doc matches the design decisions and
      links sub-issues #610–#615 for deferred RDIs

## 2. Bonares real-data suite

- [x] 2.1 Curate ≥2 real BonaRes/INSPIRE source records that together cover distinct input features (e.g.
      contacts/keywords/spatial/online resources as available), map them through the real inspire client path, and
      commit RO-Crates under `fixtures/arc_export/bonares/<case>/` with a short coverage note (README or docs section) —
      verify files are non-synthetic mapped crates
- [x] 2.2 Keep the existing bonares smoke crate (or relocate under `bonares/smoke/` only if discovery from 1.1 is
      updated in the same change) — verify both smoke and real cases are collected

## 3. Integration

- [x] 3.1 Run `uv run pytest -m system_local middleware/harvester/tests/system_local -v` with Docker and confirm all
      discovered fixtures pass `arc-export`; run `openspec validate real-data-arc-export-fixtures` — verify both green
