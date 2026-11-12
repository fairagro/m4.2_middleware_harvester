# Proposal

## Why

Issue #615 lands the deferred **phenoroam** real-data arc-export suite under the #600/#616 contract: PhenoRoam’s
OAI-PMH + `phenoroam_xml` / `phenoroam_general` path stresses sensor/geodata-shaped records (bbox, datafile-link
comments, study-parent titles, contacts) that sibling Schema.org / MODS / Regal suites do not cover. Stacking on the
nested fixture tip lets `system_local` gate production-like PhenoRoam RO-Crates without inventing a synthetic smoke.

## What Changes

- Commit a **multi-case** real-data RO-Crate set under
  `middleware/harvester/tests/fixtures/arc_export/phenoroam/<case-id>/` (folder id `phenoroam`), generated via the live
  client path (`oai_pmh` + `phenoroam_xml` + `phenoroam_general`), with emails redacted and a folder README describing
  covered features
- No root smoke crate (none exists today; do not invent one — lock-in D1)
- Update `docs/arc-export-fixtures.md` status row for phenoroam from deferred to landed
- Extend `arc-export-fixtures` OpenSpec with a phenoroam multi-case scenario (parallel to bonares / edal / publisso /
  plabipd / openagrar)
- Tighten `system_local` presence assertions for phenoroam nested cases (mirror siblings)

## Non-goals

- Landing the remaining deferred suite sradi (#612)
- Changing OAI-PMH, `phenoroam_xml`, or `phenoroam_general` behaviour unless a generated crate fails `arc-export` for a
  real mapping bug
- Committing a large OAI harvest dump
- Inventing a synthetic phenoroam smoke crate

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `arc-export-fixtures`: require a landed multi-case real-data suite for **phenoroam** with documented feature coverage

## Impact

- Fixtures + docs + `system_local` tests under `middleware/harvester/`
- Depends on nested discovery from #600/#616
- Live fetch of `https://phenoroam.phenorob.de/geonetwork/srv/eng/oaipmh` during generation (not at CI runtime once
  crates are committed)
- Docker + pinned `arc-export` for `system_local` validation (unchanged)
