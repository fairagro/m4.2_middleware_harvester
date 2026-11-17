# Proposal

## Why

Issue #611 lands the deferred **publisso** real-data arc-export suite under the #600/#616 contract: Regal `/find`
JSON-LD has agent/given-name, license, subject/DDC, and funding edges that already stress `arc-export` and are not
covered by the synthetic publisso smoke crate. Stacking on the nested fixture tip (with bonares + edal) lets
`system_local` gate production-like PUBLISSO RO-Crates without waiting for remaining deferred RDIs.

## What Changes

- Commit a **multi-case** real-data RO-Crate set under
  `middleware/harvester/tests/fixtures/arc_export/publisso/<case-id>/` (folder id `publisso`), generated via the live
  publisso client path (`regal_find` + `RegalMapper`), with emails redacted and a folder README describing covered
  features
- Keep the existing root smoke crate unless this slice explicitly replaces it
- Update `docs/arc-export-fixtures.md` status row for publisso from deferred to landed
- Extend `arc-export-fixtures` OpenSpec with a publisso multi-case scenario (parallel to bonares / edal)
- Optionally tighten `system_local` presence assertions for publisso nested cases (mirror bonares/edal)

## Non-goals

- Landing sradi / plabipd / openagrar-live / phenoroam suites (#612–#615)
- Changing Regal mapper behaviour unless a generated crate fails `arc-export` for a real mapping bug
- Full `/find` dump of PUBLISSO (~92 records)

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `arc-export-fixtures`: require a landed multi-case real-data suite for **publisso** with documented feature coverage

## Impact

- Fixtures + docs + `system_local` tests under `middleware/harvester/`
- Depends on nested discovery from #600/#616
- Live `/find` against `https://frl.publisso.de/find` during generation (not at CI runtime once crates are committed)
- Docker + pinned `arc-export` for `system_local` validation (unchanged)
