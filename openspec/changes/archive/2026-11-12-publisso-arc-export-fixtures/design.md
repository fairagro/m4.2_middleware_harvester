# Design

## Context

See proposal.md — Why. Stacks on `build/issue-600-real-arc-export-fixtures` (#616 tip, including merged #620 edal):
nested `<rdi>/<case-id>/ro-crate-metadata.json` discovery and bonares/edal real-data patterns already exist. Active
publisso harvest config lives in `dev_environment/config.all-rdis.yaml` (`rdi: publisso`, `regal_find` →
`https://frl.publisso.de/find`, `resource_base_url`, `jsonld` context pin, `regal_general`; robots disabled for
`/find`).

## Goals / Non-Goals

**Goals**

- Land 2–4 curated real publisso RO-Crates that collectively hit distinct Regal edges (not a full `/find` dump)
- Document coverage in `fixtures/arc_export/publisso/README.md` and flip the status table in
  `docs/arc-export-fixtures.md`
- Keep `system_local` + pinned `arc-export` green; mirror edal/bonares multi-case assertion for publisso
- Preserve existing root smoke crate

**Non-Goals (design-level)**

- Runtime `/find` harvest inside CI (fixtures are committed artifacts)
- Mapper refactors unless a generated crate fails `arc-export` for a real mapping bug

## Decisions

1. **Case identity = Regal `@id` / FRL token** (e.g. `frl:…` sanitized to a filesystem-safe dir name), one directory per
   case — parallel to bonares UUIDs and edal DOI slugs.
2. **Generation = live client path (C1):** query `/find` (or fetch known resource JSON-LD), map with `RegalMapper` / the
   configured publisso stack, serialize RO-Crate JSON, redact emails to `redacted@example.invalid`, commit.
3. **Breadth target (B1):** complementary cases such as (a) person contacts with given-name / agent edge, (b) license,
   (c) subjects±DDC or funding / org-heavy record — drop a slot if live data cannot supply it without expanding scope.
4. **Stacking (A1):** implement on #611 branch whose base is #600 tip; draft PR base = that branch until #616 merges to
   `main`, then retarget/rebase as needed.
5. **Spec delta:** extend `arc-export-fixtures` real-data breadth requirement with a publisso multi-case scenario.

**Alternatives considered**

- Flat single smoke-only update on `main` — rejected (fails “set” AC and nested contract).
- Replay-only unit Regal graphs — useful as supplement; primary SoT remains live-mapped crates for #611 AC.

## Risks / Trade-offs

- **[Live API drift / robots]** → Config already sets `respect_robots_txt: false` for `/find`; curate a small allowlist;
  commit artifacts so CI is offline.
- **[PII in crates]** → Redact emails/phones; note redactions in README.
- **[Agent/given-name failures]** → Prefer records that map successfully; if a chosen record fails closed on given-name
  rules, swap for another live id rather than weakening the mapper in this PR.
- **[Merge base]** → If #616 rebases, rebase #611; avoid merging #611 to `main` before nested discovery lands.

## Migration Plan

1. Propose/apply on stacked branch; user commits.
2. Draft PR targeting #600 branch (or `main` after #616 merges).
3. Archive OpenSpec change after this slice is ready.

## Open Questions

- Exact FRL ids / case dirs chosen during apply (resolved by live curation, not by spec).
