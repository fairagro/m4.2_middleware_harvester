# Design

## Context

See proposal.md — Why. Stacks on `build/issue-600-real-arc-export-fixtures` (#616 tip, including openagrar #614): nested
`<rdi>/<case-id>/ro-crate-metadata.json` discovery already exists. Active phenoroam harvest config lives in
`dev_environment/config.all-rdis.yaml` (`rdi: phenoroam`, OAI-PMH endpoint
`https://phenoroam.phenorob.de/geonetwork/srv/eng/oaipmh`, `metadata_prefix: phenoroam`, `phenoroam_xml`,
`phenoroam_general`). No root smoke crate exists for this RDI.

## Goals / Non-Goals

**Goals**

- Land 2–4 curated real PhenoRoam RO-Crates that collectively hit distinct sensor/geodata edges (not a harvest dump)
- Document coverage in `fixtures/arc_export/phenoroam/README.md` and flip the status table in
  `docs/arc-export-fixtures.md`
- Keep `system_local` + pinned `arc-export` green; mirror sibling multi-case assertion for phenoroam
- Nested cases only — do not invent a synthetic smoke (lock-in D1)

**Non-Goals (design-level)**

- Runtime live OAI harvest inside CI (fixtures are committed artifacts)
- Mapper / protocol refactors unless a generated crate fails `arc-export` for a real mapping bug

## Decisions

1. **Case identity = OAI / item UUID** (e.g. `fc207e68-d7a9-484d-b2f7-e1ee40d5dd66`) as the nested directory name — one
   directory per curated record. Prefer stable catalog UUIDs from `ListIdentifiers` / `item_uuid`.
2. **Generation = live client path (B1):** discover via OAI-PMH (`metadataPrefix=phenoroam`), parse with
   `PhenoroamXmlParser`, map with `PhenoroamMapper`, serialize RO-Crate JSON, redact emails to
   `redacted@example.invalid`, commit. Unit XML fixtures may guide edge selection but are not the SoT.
3. **Breadth target (C1):** complementary cases such as (a) bbox present, (b) multi-Person contacts with affiliation /
   email, (c) keywords + license, (d) datafile links and/or study-parent investigation titles — drop a slot if live data
   cannot supply it without expanding scope. Aim for ≥2 nested cases.
4. **No smoke (D1):** do not add `fixtures/arc_export/phenoroam/ro-crate-metadata.json`.
5. **Stacking (A1):** implement on #615 branch whose base is #600 tip; draft PR base = that branch until #616 merges to
   `main`.
6. **Spec delta:** extend `arc-export-fixtures` real-data breadth requirement with a phenoroam multi-case scenario.

**Alternatives considered**

- Invent a synthetic smoke (D2) — rejected by lock-in D1; nested cases alone satisfy presence once landed.
- Unit-fixture-only generation (B2) — useful as supplement; primary SoT remains live OAI for #615 AC.

## Risks / Trade-offs

- **[Live OAI / GeoNetwork availability]** → Curate a small allowlist; commit artifacts so CI is offline; fall back to
  unit XML only if listing is blocked during apply (still real captured shapes, not invented Investigations).
- **[PII in crates]** → Redact emails; note redactions in README.
- **[Mapper / arc-export gaps]** → Prefer failing-test-first; fix mapper only for real export bugs; otherwise split via
  create-issue.
- **[Merge base]** → If #616 rebases, rebase #615; avoid merging #615 to `main` before nested discovery lands.

## Migration Plan

1. Propose/apply on stacked branch; user commits.
2. Draft PR targeting #600 branch (or `main` after #616 merges).
3. Archive OpenSpec change after this slice is ready.

## Open Questions

- Exact catalog UUIDs chosen during apply (resolved by live curation, not by spec).
