# Proposal

## Why

Issue #612 lands the deferred **sradi** real-data arc-export suite under the #600 contract: SRADI is the first
ckanext-dcat / DCAT-AP path (`dcat_ap` → `jsonld` → `ckanext_dcat`), stressing Hydra-paginated catalog shapes, CKAN
group filtering, distribution/format edges, and spatial WKT that sibling Schema.org / Regal / MODS / PhenoRoam suites do
not cover. Landing nested fixtures lets `system_local` gate production-like SRADI RO-Crates without inventing a
synthetic smoke.

## What Changes

- Commit a **multi-case** real-data RO-Crate set under `middleware/harvester/tests/fixtures/arc_export/sradi/<case-id>/`
  (folder id `sradi`), generated via the live all-rdis client path (`dcat_ap` + `JsonLdParser` + `ckanext_dcat`), with
  emails redacted and a folder README describing covered features
- No root smoke crate (none exists today; do not invent one)
- Update `docs/arc-export-fixtures.md` status row for sradi from deferred to landed
- Extend `arc-export-fixtures` OpenSpec with a sradi multi-case scenario (parallel to bonares / edal / publisso /
  plabipd / openagrar / phenoroam)
- Tighten `system_local` presence assertions for sradi nested cases (mirror siblings)

## Non-goals

- Changing `dcat_ap`, `JsonLdParser`, or `ckanext_dcat` behaviour unless a generated crate fails `arc-export` for a real
  mapping bug
- Committing a large Hydra harvest dump or inventing a synthetic sradi smoke crate
- Fixing upstream SRADI DCAT graphs that omit `dct:license` (fixtures may retain ARCtrl default when the source has no
  license — real-source behaviour after #530)

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `arc-export-fixtures`: require a landed multi-case real-data suite for **sradi** with documented feature coverage

## Impact

- Fixtures + docs + `system_local` tests under `middleware/harvester/`
- Live fetch of `https://agrihub.gis.lrg.tum.de/catalog.jsonld?fq=groups:dataset` during generation (not at CI runtime
  once crates are committed)
- Docker + pinned `arc-export` for `system_local` validation (unchanged)
