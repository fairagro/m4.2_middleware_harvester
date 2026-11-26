# Design

## Context

See proposal.md — Why. Nested `<rdi>/<case-id>/ro-crate-metadata.json` discovery already exists on `main`. Active sradi
harvest config lives in `dev_environment/config.all-rdis.yaml` (`rdi: sradi`, `dcat_ap` entry
`https://agrihub.gis.lrg.tum.de/catalog.jsonld?fq=groups:dataset`, `jsonld`, `ckanext_dcat`). No root smoke crate exists
for this RDI. Sibling suites (bonares / edal / publisso / plabipd / openagrar / phenoroam) already land the multi-case
pattern.

## Goals / Non-Goals

**Goals**

- Land 2–4 curated real SRADI RO-Crates that collectively hit distinct DCAT-AP / ckanext-dcat edges (not a Hydra dump)
- Document coverage in `fixtures/arc_export/sradi/README.md` and flip the status table in `docs/arc-export-fixtures.md`
- Keep `system_local` + pinned `arc-export` green; mirror sibling multi-case assertion for sradi
- Nested cases only — do not invent a synthetic smoke

**Non-Goals (design-level)**

- Runtime live agrihub harvest inside CI (fixtures are committed artifacts)
- Mapper / protocol refactors unless a generated crate fails `arc-export` for a real mapping bug
- Upstream SRADI license completeness (missing `dct:license` → ARCtrl default is acceptable real-source behaviour)

## Decisions

1. **Case identity = filesystem-safe CKAN package / dataset slug** derived from the `dcat:Dataset` IRI (or
   `ckanext_dcat` Investigation identifier slug when shorter). One directory per curated record.
2. **Generation = live client path:** discover via Hydra-paginated `dcat_ap` against the all-rdis entry URL (group
   `dataset` filter kept), parse with `JsonLdParser`, map with `CkanextDcatMapper`, serialize RO-Crate JSON, redact
   emails to `redacted@example.invalid`, commit. Unit DCAT graphs may guide edge selection but are not the SoT.
3. **Breadth target:** complementary cases such as (a) multi-distribution / formats, (b) spatial WKT / geometry, (c) org
   publisher/contact unwrap, (d) landing page / source identifier, (e) with vs without `dcterms:license` when live data
   supplies both — drop a slot if live data cannot supply it without expanding scope. Aim for ≥2 nested cases.
4. **No smoke:** do not add `fixtures/arc_export/sradi/ro-crate-metadata.json`.
5. **Branch:** `build/issue-612-sradi-arc-export-fixtures` from `main` (sibling suites already merged).
6. **Spec delta:** extend `arc-export-fixtures` real-data breadth requirement with a sradi multi-case scenario.

**Alternatives considered**

- Invent a synthetic smoke — rejected; nested cases alone satisfy presence once landed (same as phenoroam).
- Unit-fixture-only generation — useful as supplement; primary SoT remains live agrihub for #612 AC.
- Case id = raw URL-encoded IRI — rejected as noisy; prefer package slug / sanitized identifier.

## Risks / Trade-offs

- **[Live agrihub / Hydra availability]** → Curate a small allowlist; commit artifacts so CI is offline; if listing is
  blocked during apply, capture a short archived Hydra page offline still from real responses (not invented
  Investigations).
- **[Missing licenses in DCAT]** → Document ARCtrl default when source omits `dct:license`; do not invent license text.
- **[PII in crates]** → Redact emails; note redactions in README.
- **[Mapper / arc-export gaps]** → Prefer failing-test-first; fix mapper only for real export bugs; otherwise split via
  create-issue.

## Migration Plan

1. Propose/apply on the issue branch; user commits.
2. Draft PR targeting `main`.
3. Archive OpenSpec change after this slice is ready.

## Open Questions

- Exact package slugs chosen during apply (resolved by live curation, not by spec).
