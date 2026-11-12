# Proposal

## Why

Issue #613 lands the deferred **plabipd** real-data arc-export suite under the #600/#616 contract: PlabiPD’s pubplant
JSON-array dump is schema.org-shaped but stresses composite discovery identifiers (shared DOIs across distinct genome
records), Organization-only vs multi-Person creators, and dump-level keyword/license edges that the synthetic openagrar
smoke crate does not cover. Stacking on the nested fixture tip (bonares + edal + publisso) lets `system_local` gate
production-like PlabiPD RO-Crates without waiting for remaining deferred RDIs.

## What Changes

- Commit a **multi-case** real-data RO-Crate set under
  `middleware/harvester/tests/fixtures/arc_export/plabipd/<case-id>/` (folder id `plabipd`), generated via the live
  plabipd client path (`pubplant_json_array` + `JsonLdParser` + `schema_org_general`), with emails redacted and a folder
  README describing covered features
- No root smoke crate is required for this RDI today (none exists); do not invent a synthetic smoke solely for this
  slice
- Update `docs/arc-export-fixtures.md` status row for plabipd from deferred to landed
- Extend `arc-export-fixtures` OpenSpec with a plabipd multi-case scenario (parallel to bonares / edal / publisso)
- Optionally tighten `system_local` presence assertions for plabipd nested cases (mirror bonares/edal/publisso)

## Non-goals

- Landing sradi / openagrar-live / phenoroam suites (#612, #614–#615)
- Changing pubplant protocol or schema.org mapper behaviour unless a generated crate fails `arc-export` for a real
  mapping bug
- Committing a large slice of the ~2335-record `genomes.json` dump

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `arc-export-fixtures`: require a landed multi-case real-data suite for **plabipd** with documented feature coverage

## Impact

- Fixtures + docs + `system_local` tests under `middleware/harvester/`
- Depends on nested discovery from #600/#616
- Live fetch of `https://raw.githubusercontent.com/usadellab/pubplant2schemaorg/gh-pages/genomes.json` during generation
  (not at CI runtime once crates are committed)
- Docker + pinned `arc-export` for `system_local` validation (unchanged)
