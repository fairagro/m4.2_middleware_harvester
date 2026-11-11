# Design

## Context

See proposal.md — Why. This change stacks on `build/issue-600-real-arc-export-fixtures` (#616): nested
`<rdi>/<case-id>/ro-crate-metadata.json` discovery and the bonares real-data pattern already exist on that tip. Active
edal harvest config lives in `dev_environment/config.all-rdis.yaml` / `config.yaml` (`rdi: edal`, sitemap
`https://doi.ipk-gatersleben.de/sitemap.xml`, Schema.org JSON-LD + placeholders for e!DAL license templates).

## Goals / Non-Goals

**Goals**

- Land 2–4 curated real edal RO-Crates that collectively hit distinct e!DAL edges (not a full sitemap dump)
- Document coverage in `fixtures/arc_export/edal/README.md` and flip the status table in `docs/arc-export-fixtures.md`
- Keep `system_local` + pinned `arc-export` green; mirror bonares multi-case assertion for edal when useful

**Non-Goals (design-level)**

- Runtime harvest of e!DAL inside CI (fixtures are committed artifacts)
- Mapper refactors unless a generated crate fails `arc-export` for a real mapping bug

## Decisions

1. **Case identity = stable source token** (DOI slug or harvest identifier), one directory per case — same as bonares
   UUIDs. Prefer DOI-derived folder names when the Dataset `@id` / DOI is the natural key (`10.5447/ipk/…` → sanitized
   dir name).
2. **Generation = live client path (C1):** run the configured edal generic/schema.org mapping against selected live
   landing pages (or a short harvest capped by id/DOI allowlist), serialize RO-Crate JSON, redact emails to
   `redacted@example.invalid`, commit. Do not invent synthetic Investigations.
3. **Breadth target (B1):** aim for complementary cases, e.g. (a) person + ORCID and/or flat address, (b) license /
   placeholder quirk, (c) org-only or DOI/`@id` without Person — drop a slot if live data cannot supply it without
   expanding scope.
4. **Stacking (A1):** implement on #610 branch whose base is #600 tip; draft PR base = that branch until #616 merges to
   `main`, then retarget/rebase as needed.
5. **Spec delta:** extend `arc-export-fixtures` real-data breadth requirement with an edal multi-case scenario rather
   than a new capability.

**Alternatives considered**

- Flat single `edal/ro-crate-metadata.json` on current `main` — rejected (fails “set” AC and nested contract).
- Replay only in-repo HTML fixtures — useful as supplement; primary SoT remains live-mapped crates for #610 AC.

## Risks / Trade-offs

- **[Live site drift / rate limit]** → Curate a small allowlist; respect Crawl-delay; commit artifacts so CI is offline.
- **[PII in crates]** → Redact emails/phones; note redactions in README.
- **[Large JSON]** → Prefer single-digit cases; Git LFS only if multi‑MB.
- **[Merge base]** → If #616 rebases, rebase #610; avoid merging #610 to `main` before nested discovery lands.

## Migration Plan

1. Propose/apply on stacked branch; user commits.
2. Draft PR targeting #600 branch (or `main` after #616 merges).
3. Archive OpenSpec change after merge of this slice.

## Open Questions

- Exact DOIs / case ids chosen during apply (resolved by live curation, not by spec).
