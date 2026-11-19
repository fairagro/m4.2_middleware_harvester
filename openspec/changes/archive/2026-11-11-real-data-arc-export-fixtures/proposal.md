# Proposal

## Why

Issue #474 shipped a `system_local` arc-export gate with **minimal** hand-built RO-Crate fixtures. Those prove Docker /
CI / PATH wiring, but they do **not** exercise real harvested/mapped payloads. DataHUB-breaking edge cases (contacts,
licenses, keywords, spatial, nested plugin shapes, …) can still slip through.

Operators need confidence that **real RDI data** survives the client pipeline through `arc-export`. Technology family
(INSPIRE, Schema.org, Regal, DCAT, OAI-PMH, …) is secondary: even RDIs that share a mapper can emit different field
shapes. Active harvest targets are those enabled in `dev_environment/config.all-rdis.yaml` (plus deferred OpenAgrar live
path tracked separately).

## What Changes

- Strengthen the `arc-export-fixtures` capability so each **active RDI** has a **set** of RO-Crate fixtures derived from
  real source records mapped through the real client path, covering that RDI’s input feature breadth (documented per
  file).
- Keep the existing minimal per-family smoke crates as inexpensive path checks alongside real-data sets (do not delete
  them in this change unless a real set fully supersedes a smoke file in the same folder).
- Document generation/redaction/LFS rules in `docs/arc-export-fixtures.md`.
- **This change’s implementation slice:** bonares (INSPIRE/CSW) real-data suite + shared docs/gate wiring. Other active
  RDIs are split to sub-issues of #600 (#610–#615).

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `arc-export-fixtures`: require real-data multi-fixture sets per active RDI (not only one synthetic representative per
  mapper family); document coverage; keep `system_local` / CI contracts; allow coexistence with smoke fixtures.

## Impact

- Fixtures under `middleware/harvester/tests/fixtures/arc_export/<rdi>/`
- `docs/arc-export-fixtures.md`
- Possibly small test helper / discovery changes under `middleware/harvester/tests/system_local/`
- No change to harvest runtime behaviour; gate-only + docs
- Follow-up implementation: #610 edal, #611 publisso, #612 sradi, #613 plabipd, #614 openagrar, #615 phenoroam
