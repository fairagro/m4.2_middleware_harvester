# Design

## Context

See proposal.md — Why. Stacks on `build/issue-600-real-arc-export-fixtures` (#616 tip, including merged #620 edal and
#627 publisso): nested `<rdi>/<case-id>/ro-crate-metadata.json` discovery already exists. Active plabipd harvest config
lives in `dev_environment/config.all-rdis.yaml` (`rdi: plabipd`, `pubplant_json_array` →
`https://raw.githubusercontent.com/usadellab/pubplant2schemaorg/gh-pages/genomes.json`, `jsonld` context pin
`http://schema.org`, `schema_org_general`).

## Goals / Non-Goals

**Goals**

- Land 2–4 curated real plabipd RO-Crates that collectively hit distinct pubplant edges (not a dump dump)
- Document coverage in `fixtures/arc_export/plabipd/README.md` and flip the status table in
  `docs/arc-export-fixtures.md`
- Keep `system_local` + pinned `arc-export` green; mirror edal/bonares/publisso multi-case assertion for plabipd

**Non-Goals (design-level)**

- Runtime `genomes.json` harvest inside CI (fixtures are committed artifacts)
- Mapper / protocol refactors unless a generated crate fails `arc-export` for a real mapping bug

## Decisions

1. **Case identity = pubplant composite discovery id** (`{sanitized_doi}:{content_sha256[:16]}` from
   `PubplantJsonArrayProtocol._record_identifier`), filesystem-safe dir name (e.g. replace `:` with `_` if needed) — one
   directory per case. Prefer including at least one shared-DOI collision pair so composite ids are exercised.
2. **Generation = live client path (C1):** fetch `genomes.json`, select curated records, parse via `JsonLdParser`
   (`allowed_context_url: http://schema.org`) + `GeneralSchemaOrgMapper`, serialize RO-Crate JSON, redact emails to
   `redacted@example.invalid`, commit.
3. **Breadth target (B1):** complementary cases such as (a) Organization-only creator, (b) multi-Person with
   givenName/familyName, (c) shared-DOI collision sibling (same `@id`, distinct content hash) — drop a slot if live data
   cannot supply it without expanding scope.
4. **Stacking (A1):** implement on #613 branch whose base is #600 tip; draft PR base = that branch until #616 merges to
   `main`, then retarget/rebase as needed.
5. **Spec delta:** extend `arc-export-fixtures` real-data breadth requirement with a plabipd multi-case scenario.

**Alternatives considered**

- Flat single smoke-only update on `main` — rejected (fails “set” AC and nested contract; no plabipd smoke exists).
- Replay-only unit schema.org graphs — useful as supplement; primary SoT remains live-mapped crates for #613 AC.

## Risks / Trade-offs

- **[Dump size / churn]** → Curate a small allowlist; commit artifacts so CI is offline; composite ids stay stable if
  record bytes match.
- **[PII in crates]** → Redact emails/phones; note redactions in README.
- **[Merge base]** → If #616 rebases, rebase #613; avoid merging #613 to `main` before nested discovery lands.
- **[#629 localhost fix]** → Optional; not required for plabipd. Tip may lag that follow-up until #629 merges into #600.

## Migration Plan

1. Propose/apply on stacked branch; user commits.
2. Draft PR targeting #600 branch (or `main` after #616 merges).
3. Archive OpenSpec change after this slice is ready.

## Open Questions

- Exact composite case dirs chosen during apply (resolved by live curation, not by spec).
