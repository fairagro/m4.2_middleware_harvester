# Design

## Context

See proposal.md — Why. Stacks on `build/issue-600-real-arc-export-fixtures` (#616 tip, including edal / publisso /
plabipd): nested `<rdi>/<case-id>/ro-crate-metadata.json` discovery already exists. Preferred OpenAgrar harvest config
is commented in `dev_environment/config.all-rdis.yaml` (`rdi: openagrar`, `mycore_rest` entry
`https://www.openagrar.de/api/v2/objects?category=state:published&type=mods`, `mods_xml`, `mods_general`). Live `/api/`
is not PoW-gated; HTML `/receive` and Solr remain gated (#271). A root smoke crate currently exists at
`fixtures/arc_export/openagrar/ro-crate-metadata.json`.

## Goals / Non-Goals

**Goals**

- Land 2–4 curated real OpenAgrar MODS RO-Crates that collectively hit distinct MODS edges (not a harvest dump)
- Remove the openagrar root smoke crate so the suite is nested real-data only (lock-in D2); keep RDI id `openagrar` via
  nested cases for the three-family presence check
- Document coverage in `fixtures/arc_export/openagrar/README.md` and flip the status table in
  `docs/arc-export-fixtures.md`
- Keep `system_local` + pinned `arc-export` green; mirror sibling multi-case assertion for openagrar

**Non-Goals (design-level)**

- Runtime live OpenAgrar harvest inside CI (fixtures are committed artifacts)
- Enabling `openagrar-fixture` or Schema.org HTML as the real-data SoT
- Mapper / protocol refactors unless a generated crate fails `arc-export` for a real mapping bug

## Decisions

1. **Case identity = MyCoRe object id** (e.g. `openagrar_mods_00110150`) as the nested directory name — one directory
   per curated record. Prefer ids that stay stable across list pagination.
2. **Generation = live client path (B1):** list/fetch via `MycoreRestProtocol` against the live entry URL, parse with
   `ModsXmlParser`, map with `ModsGeneralMapper`, serialize RO-Crate JSON, redact emails/phones to
   `redacted@example.invalid` (or omit), commit. Do not use `openagrar-fixture` HTTP stand-in as the primary source.
3. **Breadth target (C1):** complementary cases such as (a) multi-Person creators with affiliation, (b) organization /
   corporate name edges when present, (c) license + subjects/keywords, (d) title / identifier / related-item shape
   differences — drop a slot if live data cannot supply it without expanding scope. Aim for ≥2 nested cases.
4. **Smoke removal (D2):** delete `fixtures/arc_export/openagrar/ro-crate-metadata.json` in the same apply as nested
   cases land. Update docs so openagrar is no longer listed among RDIs that keep an optional root smoke.
5. **Stacking (A1):** implement on #614 branch whose base is #600 tip; draft PR base = that branch until #616 merges to
   `main`, then retarget/rebase as needed.
6. **Spec delta:** extend `arc-export-fixtures` real-data breadth requirement with an openagrar multi-case scenario that
   forbids keeping the root smoke once the suite lands.

**Alternatives considered**

- Keep smoke alongside nested cases (D1) — rejected by lock-in D2; nested cases still satisfy family presence.
- Archived-only MODS from `dev_environment/fixtures/openagrar/api/v2/objects/` (2 records) — useful as a fallback if
  live listing fails during apply; primary SoT remains live B1.
- Schema.org / fixture-server HTML path — rejected (does not satisfy #614 / docs).

## Risks / Trade-offs

- **[Live API availability / selection time]** → Curate a small allowlist; commit artifacts so CI is offline; fall back
  to the two archived live-captured MODS objects only if listing is blocked during apply (still real MODS, not
  synthetic).
- **[PII in crates]** → Redact emails/phones; note redactions in README.
- **[MODS→ARC / arc-export gaps]** → Prefer failing-test-first; fix mapper only for real export bugs; otherwise split
  via create-issue.
- **[Merge base]** → If #616 rebases, rebase #614; avoid merging #614 to `main` before nested discovery lands.
- **[Three-family smoke wording]** → After D2, docs/tests must not require an openagrar _root_ smoke — only RDI id
  presence via nested cases.

## Migration Plan

1. Propose/apply on stacked branch; user commits.
2. Draft PR targeting #600 branch (or `main` after #616 merges).
3. Archive OpenSpec change after this slice is ready.

## Open Questions

- Exact MODS object ids chosen during apply (resolved by live curation, not by spec).
