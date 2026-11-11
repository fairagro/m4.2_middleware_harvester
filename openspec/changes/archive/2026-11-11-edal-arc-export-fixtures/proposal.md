# Proposal

## Why

Issue #610 lands the deferred **edal** real-data arc-export suite under the #600/#616 contract: e!DAL’s Schema.org
HTML/JSON-LD path has distinct placeholder, license-template, address, ORCID, and DOI/`@id` quirks that the openagrar
smoke crate does not exercise. Stacking on the nested fixture layout lets `system_local` gate production-like edal
RO-Crates without waiting for every other deferred RDI.

## What Changes

- Commit a **multi-case** real-data RO-Crate set under `middleware/harvester/tests/fixtures/arc_export/edal/<case-id>/`
  (folder id `edal` matching harvest config), generated via the live edal client path, with emails redacted and a folder
  README describing covered features
- Update `docs/arc-export-fixtures.md` status row for edal from deferred to landed
- Extend `arc-export-fixtures` OpenSpec with an edal multi-case scenario (parallel to bonares)
- Optionally tighten `system_local` presence assertions for edal nested cases (mirror bonares multi-case check)
- Keep any future edal smoke crate optional; do not remove other RDI smoke fixtures

## Non-goals

- Landing publisso / sradi / plabipd / openagrar-live / phenoroam suites (#611–#615)
- Changing Schema.org mapper behaviour (fixtures only unless a crate exposes a real mapping/`arc-export` bug)
- Full sitemap dump of e!DAL (~338 records / Crawl-delay: 1)

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `arc-export-fixtures`: require a landed multi-case real-data suite for **edal** with documented feature coverage

## Impact

- Fixtures + docs + `system_local` tests under `middleware/harvester/`
- Depends on nested discovery from #600/#616 (`<rdi>/<case-id>/ro-crate-metadata.json`)
- Live harvest against `https://doi.ipk-gatersleben.de/` during generation (not at CI runtime once crates are committed)
- Docker + pinned `arc-export` for `system_local` validation (unchanged)
