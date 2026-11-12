# Proposal

## Why

Issue #614 lands the deferred **openagrar** real-data arc-export suite under the #600/#616 contract: the preferred
OpenAgrar client path is live MyCoRe REST + MODS (`mycore_rest` → `mods_xml` → `mods_general`), not the PoW-gated HTML
Schema.org export or the local `openagrar-fixture` stand-in. Stacking on the nested fixture tip (bonares + edal +
publisso + plabipd) lets `system_local` gate production-like OpenAgrar RO-Crates and retire the synthetic smoke crate
for this RDI.

## What Changes

- Commit a **multi-case** real-data RO-Crate set under
  `middleware/harvester/tests/fixtures/arc_export/openagrar/<case-id>/` (folder id `openagrar`), generated via the live
  OpenAgrar path (`mycore_rest` + `mods_xml` + `mods_general`), with emails/phones redacted and a folder README
  describing covered features
- **BREAKING (fixtures only):** remove the root smoke crate `fixtures/arc_export/openagrar/ro-crate-metadata.json` so
  the suite is real-data nested cases only (lock-in D2); `system_local` three-family presence still sees RDI id
  `openagrar` via nested cases
- Update `docs/arc-export-fixtures.md` status row for openagrar (live / MODS) from deferred to landed; clarify that
  `openagrar-fixture` remains a local stand-in only
- Extend `arc-export-fixtures` OpenSpec with an openagrar multi-case scenario (parallel to bonares / edal / publisso /
  plabipd)
- Tighten `system_local` presence assertions for openagrar nested cases (mirror siblings)

## Non-goals

- Landing sradi / phenoroam suites (#612, #615)
- Treating `openagrar-fixture` / HTML Schema.org / Solr discovery as the real-data SoT for this slice
- Changing `mycore_rest`, `mods_xml`, or `mods_general` behaviour unless a generated crate fails `arc-export` for a real
  mapping bug
- Uncommenting / enabling the live OpenAgrar repo in default operator configs beyond what’s needed to document the
  generation path
- Committing a large harvest dump of OpenAgrar MODS objects

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `arc-export-fixtures`: require a landed multi-case real-data suite for **openagrar** (live MODS path) with documented
  feature coverage; openagrar smoke-only is no longer sufficient once the suite lands

## Impact

- Fixtures + docs + `system_local` tests under `middleware/harvester/`
- Depends on nested discovery from #600/#616
- Live fetch of `https://www.openagrar.de/api/v2/objects…` during generation (not at CI runtime once crates are
  committed); `/api/` is not PoW-gated (#271 / #503)
- Docker + pinned `arc-export` for `system_local` validation (unchanged)
